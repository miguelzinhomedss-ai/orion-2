import importlib
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'orion 2'))
import voz
from voz_entrada import ReconhecedorVoz


class VozTests(unittest.TestCase):
    def setUp(self):
        self.backend = patch.object(voz.config, 'TTS_BACKEND', 'offline')
        self.backend.start()
        self.addCleanup(self.backend.stop)

    def motor(self):
        motor = Mock()
        motor.isBusy.return_value = False
        motor.getProperty.return_value = [
            types.SimpleNamespace(id='en', name='David', languages=['en-US'], gender='male'),
            types.SimpleNamespace(id='pt', name='Maria', languages=['pt-BR'], gender='female'),
            types.SimpleNamespace(id='br', name='Antonio', languages=['pt-BR'], gender='male')]
        return motor

    def test_sintese_portugues_masculino(self):
        motor = self.motor()
        with patch.dict(sys.modules, pyttsx3=Mock(init=Mock(return_value=motor))):
            self.assertTrue(voz.falar('Olá, Miguel!'))
        motor.setProperty.assert_any_call('voice', 'br')
        motor.say.assert_called_once_with('Olá, Miguel!')
        motor.startLoop.assert_called_once_with(False)
        motor.endLoop.assert_called_once()
        motor.stop.assert_called_once()

    def test_falha_audio_preserva_texto(self):
        motor = self.motor()
        motor.startLoop.side_effect = OSError('sem dispositivo')
        with patch.dict(sys.modules, pyttsx3=Mock(init=Mock(return_value=motor))):
            self.assertFalse(voz.falar('Resposta'))
        motor.stop.assert_called_once()

    def test_dependencia_opcional(self):
        with patch.dict(sys.modules, pyttsx3=None):
            self.assertFalse(voz.falar('Resposta'))

    def test_sem_voz_portuguesa(self):
        motor = self.motor()
        motor.getProperty.return_value = []
        with patch.dict(sys.modules, pyttsx3=Mock(init=Mock(return_value=motor))):
            self.assertFalse(voz.falar('Olá'))
        motor.say.assert_not_called()

    def test_texto_vazio(self):
        self.assertFalse(voz.falar('  '))


class EntradaTests(unittest.TestCase):
    def setUp(self):
        self.sr = types.ModuleType('speech_recognition')
        self.sr.WaitTimeoutError = type('WaitTimeoutError', (Exception,), {})
        self.sr.UnknownValueError = type('UnknownValueError', (Exception,), {})
        self.rec = Mock()
        self.rec.recognize_google.return_value = 'Orion, listar tarefas'
        self.sr.Recognizer = Mock(return_value=self.rec)
        self.sr.Microphone = Mock()
        self.sr.Microphone.return_value.__enter__ = Mock(return_value=object())
        self.sr.Microphone.return_value.__exit__ = Mock(return_value=False)
        self.patcher = patch.dict(sys.modules, speech_recognition=self.sr)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_inicializacao_sem_hardware(self):
        ReconhecedorVoz()
        self.sr.Microphone.assert_not_called()

    def test_reconhecimento_pt_br(self):
        self.assertEqual(ReconhecedorVoz().ouvir(), 'Orion, listar tarefas')
        self.rec.recognize_google.assert_called_once_with(self.rec.listen.return_value, language='pt-BR')
        self.assertEqual(self.rec.operation_timeout, 5)
        self.assertEqual(self.rec.listen.call_args.kwargs, dict(timeout=1, phrase_time_limit=5))

    def test_cancelamento_antes_de_capturar(self):
        evento = threading.Event()
        evento.set()
        self.assertIsNone(ReconhecedorVoz().ouvir(evento))
        self.sr.Microphone.assert_not_called()

    def test_cancelamento_durante_captura(self):
        evento = threading.Event()
        self.rec.listen.side_effect = lambda *a, **kw: evento.set()
        self.assertIsNone(ReconhecedorVoz().ouvir(evento))
        self.rec.recognize_google.assert_not_called()

    def test_silencio_e_fala_incompreensivel(self):
        self.rec.listen.side_effect = self.sr.WaitTimeoutError()
        self.assertIsNone(ReconhecedorVoz().ouvir())
        self.rec.listen.side_effect = None
        self.rec.recognize_google.side_effect = self.sr.UnknownValueError()
        self.assertIsNone(ReconhecedorVoz().ouvir())

    def test_sem_microfone(self):
        self.sr.Microphone.side_effect = OSError('sem dispositivo')
        with self.assertRaises(RuntimeError):
            ReconhecedorVoz().ouvir()

    def test_falha_rede(self):
        self.rec.recognize_google.side_effect = OSError('offline')
        with self.assertRaises(RuntimeError):
            ReconhecedorVoz().ouvir()


class IntegracaoTests(unittest.TestCase):
    def test_orion_inicia_sem_audio_e_preserva_tarefas(self):
        import main
        import memoria
        import config
        # Interface gráfica substituída: nenhum display, microfone ou rede real.
        with tempfile.TemporaryDirectory() as pasta, \
             patch.object(memoria, 'TASKS_FILE', str(Path(pasta) / 'tarefas.json')), \
             patch.object(memoria, 'MEMORY_FILE', str(Path(pasta) / 'memoria.json')), \
             patch('inteligencia.GROQ_API_KEY', 'chave-apenas-para-teste'), \
             patch.object(main, 'OrionInterface') as interface, \
             patch.dict(sys.modules, pyttsx3=None), \
             patch.object(voz.config, 'TTS_BACKEND', 'offline'):
            orion = main.Orion()
            interface.assert_called_once_with(orion.processar)
            self.assertIsInstance(orion.ia, main.OrionIA)
            self.assertIn('Tarefa salva', orion.processar('adicionar tarefa Comprar pão'))
            self.assertIn('Comprar pão', orion.processar('listar tarefas'))
            self.assertIn('concluída', orion.processar('concluir tarefa um'))
            self.assertIn('removida', orion.processar('remover tarefa um'))
            memoria.adicionar_memoria('Gosta de Python')
            self.assertEqual(memoria.carregar_memoria(), ['Gosta de Python'])
            with patch.object(orion.ia, 'perguntar', return_value='Olá!') as perguntar:
                self.assertEqual(orion.processar('Explique Python'), 'Olá!')
                perguntar.assert_called_once_with('Explique Python')

    def test_interface_encaminha_falha_sem_tocar_tk_na_thread(self):
        import interface
        import queue
        tela = interface.OrionInterface.__new__(interface.OrionInterface)
        tela.reconhecedor_voz = Mock()
        tela.reconhecedor_voz.ouvir.side_effect = RuntimeError('sem microfone')
        tela.eventos = queue.Queue()
        tela._ouvir_em_background(7, threading.Event(), False)
        tipo, (sessao, texto, erro, comando) = tela.eventos.get_nowait()
        self.assertEqual((tipo, sessao, texto, comando), ('escuta', 7, None, False))
        self.assertTrue(erro)


if __name__ == '__main__':
    unittest.main()
