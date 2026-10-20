"""Integração Kokoro com mocks, sem modelos, rede ou dispositivos."""
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'orion 2'))
import voz
import voz_kokoro


class IntegracaoKokoroTests(unittest.TestCase):
    def test_divisao_preserva_palavras_e_limita_primeiro_trecho(self):
        texto = ('Boa noite. ' + 'Esta é uma explicação longa, com pausas naturais e várias palavras. ' * 10)
        partes = voz_kokoro.dividir_texto(texto)
        self.assertEqual(' '.join(partes).split(), texto.split())
        self.assertLessEqual(len(partes[0]), 80)
        self.assertTrue(all(len(p) <= 160 for p in partes))
        self.assertGreater(len(partes), 2)

    def test_sem_espacos_ou_texto_vazio(self):
        self.assertEqual(voz_kokoro.dividir_texto('  '), [])
        self.assertEqual(voz_kokoro.dividir_texto('a' * 200), ['a' * 200])

    def test_sessao_persistente_e_cpu(self):
        ort, kokoro = Mock(), Mock()
        with tempfile.TemporaryDirectory() as pasta:
            modelo, vozes = Path(pasta) / 'm.onnx', Path(pasta) / 'v.bin'
            modelo.touch(); vozes.touch()
            with patch.object(voz.config, 'KOKORO_MODEL', str(modelo)), \
                 patch.object(voz.config, 'KOKORO_VOICES', str(vozes)), \
                 patch.object(voz_kokoro, '_motor', None), patch.object(voz_kokoro, '_chave', None), \
                 patch.dict(sys.modules, onnxruntime=ort, kokoro_onnx=types.SimpleNamespace(Kokoro=kokoro)):
                primeiro = voz_kokoro._carregar()
                segundo = voz_kokoro._carregar()
            self.assertIs(primeiro, segundo)
            ort.InferenceSession.assert_called_once()
            self.assertEqual(ort.InferenceSession.call_args.kwargs['providers'], ['CPUExecutionProvider'])
            self.assertEqual(ort.SessionOptions.return_value.intra_op_num_threads, 2)
            kokoro.from_session.assert_called_once()
            ort.SessionOptions.return_value.add_session_config_entry.assert_any_call(
                'session.intra_op.allow_spinning', '0')

    def test_modelo_ausente_nao_baixa_nada(self):
        with patch.object(voz_kokoro, '_motor', None), \
             patch.object(voz.config, 'KOKORO_MODEL', '/modelo-inexistente.onnx'):
            with self.assertRaises(FileNotFoundError):
                voz_kokoro._carregar()

    def test_principal_kokoro_e_alternativa_edge(self):
        with patch.object(voz.config, 'TTS_BACKEND', 'kokoro'), \
             patch.object(voz, '_falar_kokoro', return_value=True) as kokoro, \
             patch.object(voz, '_falar_online') as edge:
            self.assertTrue(voz.falar('Olá'))
            kokoro.assert_called_once_with('Olá')
            edge.assert_not_called()

    def test_ausencia_kokoro_recorre_ao_edge(self):
        with patch.object(voz.config, 'TTS_BACKEND', 'kokoro'), \
             patch.object(voz, '_falar_kokoro', side_effect=ImportError()), \
             patch.object(voz, '_falar_online') as edge:
            self.assertTrue(voz.falar('Olá'))
            edge.assert_called_once_with('Olá')

    def test_prefetch_limitado_e_reproducao_progressiva(self):
        gerados, tocados = [], []
        segunda_pronta = threading.Event()
        def gerar(texto):
            gerados.append(texto)
            if len(gerados) == 2:
                segunda_pronta.set()
            return BytesIO(b'wav simulado')
        def tocar(arquivo):
            tocados.append(arquivo)
            if len(tocados) == 1:
                self.assertTrue(segunda_pronta.wait(1))
                # O terceiro trecho só pode começar depois da primeira reprodução.
                self.assertEqual(len(gerados), 2)
        with patch.object(voz_kokoro, 'gerar_audio', side_effect=gerar), \
             patch.object(voz, '_reproduzir', side_effect=tocar):
            self.assertTrue(voz._falar_kokoro('Primeiro. Segundo. Terceiro.'))
        self.assertEqual(gerados, ['Primeiro.', 'Segundo.', 'Terceiro.'])
        self.assertEqual(len(tocados), 3)
        self.assertTrue(all(p.closed for p in tocados))

    def test_fallback_nao_repete_trechos_concluidos(self):
        def gerar(texto):
            if texto == 'Segundo.':
                raise RuntimeError('falha')
            return BytesIO(b'wav simulado')
        with patch.object(voz_kokoro, 'gerar_audio', side_effect=gerar), \
             patch.object(voz, '_reproduzir') as tocar, \
             patch.object(voz, '_falar_alternativas', return_value=True) as alternativa:
            self.assertTrue(voz._falar_kokoro('Primeiro. Segundo. Terceiro.'))
        tocar.assert_called_once()
        alternativa.assert_called_once_with('Segundo. Terceiro.')

    def test_fallback_completo_ate_offline(self):
        with patch.object(voz.config, 'TTS_BACKEND', 'kokoro'), \
             patch.object(voz, '_falar_kokoro', side_effect=RuntimeError()), \
             patch.object(voz, '_falar_online', side_effect=OSError()), \
             patch.object(voz, '_falar_offline', return_value=True) as offline:
            self.assertTrue(voz.falar('Olá'))
        offline.assert_called_once_with('Olá')

    def test_cancelar_antes_de_falar_nao_aciona_backends(self):
        evento = threading.Event()
        evento.set()
        with voz.contexto_fala(evento), \
             patch.object(voz, '_falar_kokoro') as kokoro, \
             patch.object(voz, '_falar_online') as edge, \
             patch.object(voz, '_falar_offline') as offline:
            self.assertFalse(voz.falar('Olá'))
        kokoro.assert_not_called()
        edge.assert_not_called()
        offline.assert_not_called()

    def test_cancelar_reproducao_para_player_e_libera_buffers(self):
        buffers = []
        def gerar(texto):
            audio = BytesIO(b'wav simulado')
            buffers.append(audio)
            return audio
        mixer = Mock()
        mixer.music.get_busy.return_value = True
        with patch.object(voz.config, 'TTS_BACKEND', 'kokoro'), \
             patch.object(voz_kokoro, 'gerar_audio', side_effect=gerar), \
             patch.dict(sys.modules, pygame=types.SimpleNamespace(mixer=mixer)), \
             patch.object(voz.time, 'sleep', side_effect=lambda _: voz.cancelar_fala()), \
             patch.object(voz, '_falar_alternativas') as alternativa:
            self.assertFalse(voz.falar('Primeiro. Segundo. Terceiro.'))
        alternativa.assert_not_called()
        mixer.music.stop.assert_called_once()
        mixer.music.unload.assert_called_once()
        mixer.quit.assert_called_once()
        self.assertTrue(all(b.closed for b in buffers))

    def test_cancelar_durante_inferencia_descarta_resultado(self):
        entrou, liberar = threading.Event(), threading.Event()
        buffers, resultados = [], []
        def gerar(texto):
            entrou.set()
            if not liberar.wait(2):
                raise AssertionError('timeout no teste')
            audio = BytesIO(b'wav simulado')
            buffers.append(audio)
            return audio
        with patch.object(voz.config, 'TTS_BACKEND', 'kokoro'), \
             patch.object(voz_kokoro, 'gerar_audio', side_effect=gerar), \
             patch.object(voz, '_reproduzir') as tocar, \
             patch.object(voz, '_falar_alternativas') as alternativa:
            t = threading.Thread(target=lambda: resultados.append(voz.falar('Primeiro. Segundo.')))
            t.start()
            try:
                self.assertTrue(entrou.wait(1))
                voz.cancelar_fala()
            finally:
                liberar.set()
                t.join(2)
            self.assertFalse(t.is_alive())
        self.assertEqual(resultados, [False])
        tocar.assert_not_called()
        alternativa.assert_not_called()
        self.assertTrue(all(b.closed for b in buffers))

    def test_cancelar_online_cancela_download_sem_offline(self):
        import asyncio
        entrou, encerrado = threading.Event(), threading.Event()
        resultados = []
        async def salvar(*args):
            entrou.set()
            try:
                await asyncio.Event().wait()
            finally:
                encerrado.set()
        servico = Mock(save=salvar)
        with patch.object(voz.config, 'TTS_BACKEND', 'edge'), \
             patch.dict(sys.modules, edge_tts=Mock(Communicate=Mock(return_value=servico))), \
             patch.object(voz, '_reproduzir') as tocar, \
             patch.object(voz, '_falar_offline') as offline:
            t = threading.Thread(target=lambda: resultados.append(voz.falar('Olá')))
            t.start()
            try:
                self.assertTrue(entrou.wait(1))
            finally:
                voz.cancelar_fala()
                t.join(2)
            self.assertFalse(t.is_alive())
        self.assertTrue(encerrado.is_set())
        self.assertEqual(resultados, [False])
        tocar.assert_not_called()
        offline.assert_not_called()

    def test_cancelar_pyttsx3_na_mesma_thread(self):
        motor = Mock()
        motor.isBusy.return_value = True
        motor.getProperty.return_value = [types.SimpleNamespace(
            id='pt', name='Antonio', languages=['pt-br'], gender='male')]
        motor.iterate.side_effect = lambda: voz.cancelar_fala()
        with patch.object(voz.config, 'TTS_BACKEND', 'pyttsx3'), \
             patch.dict(sys.modules, pyttsx3=Mock(init=Mock(return_value=motor))):
            self.assertFalse(voz.falar('Olá'))
        motor.stop.assert_called_once()
        motor.endLoop.assert_called_once()

    def test_interface_parar_sinaliza_resposta_antes_do_audio(self):
        import interface
        tela = interface.OrionInterface.__new__(interface.OrionInterface)
        tela.cancelamento_fala = threading.Event()
        tela.parar_fala()
        self.assertTrue(tela.cancelamento_fala.is_set())


    def test_cancelamento_na_interface_preserva_resposta_textual(self):
        import interface
        import queue
        tela = interface.OrionInterface.__new__(interface.OrionInterface)
        tela.cancelamento_fala = threading.Event()
        tela.eventos = queue.Queue()
        def responder(texto):
            tela.parar_fala()
            self.assertFalse(voz.falar('Resposta por voz'))
            return 'Resposta por texto'
        tela.responder = responder
        with patch.object(voz, '_falar_kokoro') as kokoro, \
             patch.object(voz, '_falar_online') as edge:
            tela.processar_em_background('Pergunta')
        kokoro.assert_not_called()
        edge.assert_not_called()
        self.assertEqual(tela.eventos.get_nowait(), ('resposta', ('Resposta por texto', False)))



if __name__ == '__main__':
    unittest.main()
