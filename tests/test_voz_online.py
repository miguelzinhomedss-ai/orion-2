"""Rede, player e síntese simulados; nenhum áudio ou chamada externa."""
import asyncio
from pathlib import Path
import queue
import sys
import threading
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'orion 2'))
import voz


class OnlineTests(unittest.TestCase):
    def setUp(self):
        p = patch.object(voz.config, 'TTS_BACKEND', 'edge')
        p.start()
        self.addCleanup(p.stop)

    def test_parametros_antonio(self):
        servico = Mock()
        servico.save = AsyncMock()
        construtor = Mock(return_value=servico)
        with patch.dict(sys.modules, edge_tts=types.SimpleNamespace(Communicate=construtor)):
            asyncio.run(voz._gerar_online('Olá!', Path('teste.mp3')))
        construtor.assert_called_once_with('Olá!', voice='pt-BR-AntonioNeural',
                                           rate='-8%', pitch='-5Hz',
                                           connect_timeout=5, receive_timeout=10)
        servico.save.assert_awaited_once_with('teste.mp3')

    def test_configuracoes_personalizadas(self):
        servico = Mock(save=AsyncMock())
        construtor = Mock(return_value=servico)
        with patch.dict(sys.modules, edge_tts=types.SimpleNamespace(Communicate=construtor)), \
             patch.object(voz.config, 'TTS_VOICE', 'pt-BR-FranciscaNeural'), \
             patch.object(voz.config, 'TTS_RATE', '-12%'), \
             patch.object(voz.config, 'TTS_PITCH', '-3Hz'):
            asyncio.run(voz._gerar_online('Olá!', Path('teste.mp3')))
        self.assertEqual(construtor.call_args.kwargs['voice'], 'pt-BR-FranciscaNeural')
        self.assertEqual(construtor.call_args.kwargs['rate'], '-12%')
        self.assertEqual(construtor.call_args.kwargs['pitch'], '-3Hz')

    def test_sucesso_nao_aciona_offline(self):
        with patch.object(voz, '_falar_online') as online, \
             patch.object(voz, '_falar_offline') as offline:
            self.assertTrue(voz.falar('Olá'))
        online.assert_called_once_with('Olá')
        offline.assert_not_called()

    def test_fallback_falha_rede_timeout_e_player(self):
        for erro in [OSError('offline'), TimeoutError(), RuntimeError('player')]:
            with self.subTest(erro=type(erro)), \
                 patch.object(voz, '_falar_online', side_effect=erro), \
                 patch.object(voz, '_falar_offline', return_value=True) as offline:
                self.assertTrue(voz.falar('Olá'))
                offline.assert_called_once_with('Olá')

    def test_ambos_falham(self):
        with patch.object(voz, '_falar_online', side_effect=OSError()), \
             patch.object(voz, '_falar_offline', return_value=False):
            self.assertFalse(voz.falar('Olá'))

    def test_offline_forcado(self):
        with patch.object(voz.config, 'TTS_BACKEND', 'offline'), \
             patch.object(voz, '_falar_online') as online, \
             patch.object(voz, '_falar_offline', return_value=True):
            self.assertTrue(voz.falar('Olá'))
        online.assert_not_called()

    def test_timeout_geracao_cancela_corrotina(self):
        cancelado = []
        async def lento(*args):
            try:
                await asyncio.Event().wait()
            finally:
                cancelado.append(True)
        with patch.dict(sys.modules, edge_tts=Mock(Communicate=Mock(return_value=Mock(save=lento)))), \
             patch.object(voz.config, 'TTS_TIMEOUT', 0.01):
            with self.assertRaises(TimeoutError):
                asyncio.run(voz._gerar_online('Olá', Path('teste.mp3')))
        self.assertEqual(cancelado, [True])

    def test_temporario_removido_apos_falha(self):
        caminhos = []
        async def gerar(texto, arquivo):
            caminhos.append(arquivo)
            arquivo.write_bytes(b'audio simulado')
        with patch.object(voz, '_gerar_online', side_effect=gerar), \
             patch.object(voz, '_reproduzir', side_effect=OSError('sem audio')):
            with self.assertRaises(OSError):
                voz._falar_online('Olá')
        self.assertFalse(caminhos[0].parent.exists())

    def test_player_libera_arquivo_em_falha(self):
        mixer = Mock()
        mixer.music.get_busy.side_effect = RuntimeError('falha')
        with patch.dict(sys.modules, pygame=types.SimpleNamespace(mixer=mixer)):
            with self.assertRaises(RuntimeError):
                voz._reproduzir(Path('teste.mp3'))
        mixer.music.stop.assert_called_once()
        mixer.music.unload.assert_called_once()
        mixer.quit.assert_called_once()

    def test_player_timeout(self):
        mixer = Mock()
        mixer.music.get_busy.return_value = True
        with patch.dict(sys.modules, pygame=types.SimpleNamespace(mixer=mixer)), \
             patch.object(voz.time, 'monotonic', side_effect=[0, 181]):
            with self.assertRaises(TimeoutError):
                voz._reproduzir(Path('teste.mp3'))
        mixer.music.stop.assert_called_once()
        mixer.quit.assert_called_once()

    def test_chamadas_concorrentes_serializadas(self):
        entrou = threading.Event()
        liberar = threading.Event()
        ordem = []
        def online(texto):
            ordem.append(texto)
            if texto == 'primeira':
                entrou.set()
                if not liberar.wait(2):
                    raise AssertionError('timeout no teste')
        with patch.object(voz, '_falar_online', side_effect=online):
            primeira = threading.Thread(target=voz.falar, args=('primeira',))
            segunda = threading.Thread(target=voz.falar, args=('segunda',))
            primeira.start()
            try:
                self.assertTrue(entrou.wait(1))
                segunda.start()
                self.assertEqual(ordem, ['primeira'])
            finally:
                liberar.set()
                primeira.join(2)
                if segunda.ident is not None:
                    segunda.join(2)
            self.assertFalse(primeira.is_alive())
            self.assertFalse(segunda.is_alive())
            self.assertEqual(ordem, ['primeira', 'segunda'])

    def test_interface_agenda_eventos_enquanto_resposta_fala(self):
        from interface import OrionInterface
        entrou, liberar = threading.Event(), threading.Event()
        tela = OrionInterface.__new__(OrionInterface)
        tela.encerrando = False
        tela.eventos = queue.Queue()
        tela.textos_pendentes = ['Olá']
        tela.escuta_ativa = tela.processamento_ativo = False
        tela.root = Mock()
        tela.definir_estado = Mock()
        def responder(texto):
            entrou.set()
            liberar.wait(2)
            return 'Resposta'
        tela.responder = responder
        threads = []
        criar_thread = threading.Thread
        def criar(*args, **kwargs):
            t = criar_thread(*args, **kwargs)
            threads.append(t)
            return t
        with patch('interface.threading.Thread', side_effect=criar):
            try:
                tela.consumir_eventos()
                self.assertTrue(entrou.wait(1))
                self.assertTrue(tela.processamento_ativo)
                # Tk já pode consumir novos eventos antes da resposta terminar.
                tela.root.after.assert_called_once_with(50, tela.consumir_eventos)
            finally:
                liberar.set()
                for t in threads:
                    t.join(2)
        self.assertEqual(tela.eventos.get_nowait(), ('resposta', ('Resposta', False)))


if __name__ == '__main__':
    unittest.main()
