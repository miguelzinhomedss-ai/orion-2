"""Testes do experimento sem instalar Kokoro, baixar modelos ou acessar áudio."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments' / 'kokoro'))
import testar_desempenho as desempenho
import comparar_vozes as comparador
import baixar_modelos as downloader


class Array:
    ndim = 1
    size = 24
    def __len__(self):
        return 24


class KokoroTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pasta = Path(self.temp.name)
        self.modelo, self.vozes = self.pasta / 'modelo.onnx', self.pasta / 'vozes.bin'
        self.modelo.touch()
        self.vozes.touch()
        self.motor = Mock()
        self.motor.get_voices.return_value = list(comparador.VOZES)
        self.motor.create.return_value = (Array(), 24000)
        self.kokoro = Mock()
        self.kokoro.from_session.return_value = self.motor
        self.ort = Mock()
        self.np = types.SimpleNamespace(asarray=lambda x: x,
                                       isfinite=lambda x: types.SimpleNamespace(all=lambda: True))
        def escrever(arquivo, amostras, taxa, **kwargs):
            with wave.open(arquivo, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(taxa)
                wav.writeframes(b'\0\0' * len(amostras))
        self.sf = Mock(write=Mock(side_effect=escrever))
        p = patch.dict(sys.modules, numpy=self.np, onnxruntime=self.ort,
                       soundfile=self.sf, kokoro_onnx=types.SimpleNamespace(Kokoro=self.kokoro))
        p.start()
        self.addCleanup(p.stop)

    def comparar(self, **kwargs):
        return comparador.comparar(self.modelo, self.vozes, self.pasta / 'saida', **kwargs)

    def test_duas_vozes_mesma_frase_cpu_e_wavs_separados(self):
        pasta = self.comparar()
        chamadas = self.motor.create.call_args_list
        self.assertEqual([c.args for c in chamadas], [(comparador.FRASE,), (comparador.FRASE,)])
        self.assertEqual([c.kwargs for c in chamadas], [
            {'voice': voz, 'speed': 0.95, 'lang': 'pt-br'} for voz in comparador.VOZES])
        self.assertEqual(self.ort.InferenceSession.call_args.kwargs['providers'], ['CPUExecutionProvider'])
        opcoes = self.ort.SessionOptions.return_value
        self.assertEqual(opcoes.intra_op_num_threads, 2)
        self.assertEqual(opcoes.inter_op_num_threads, 1)
        for voz in comparador.VOZES:
            with wave.open(str(pasta / f'{voz}.wav'), 'rb') as wav:
                self.assertEqual((wav.getnframes(), wav.getframerate()), (24, 24000))
        registro = json.loads((pasta / 'comparacao.json').read_text())
        self.assertEqual(registro['status'], 'concluido')
        self.assertEqual(len(registro['resultados']), 2)

    def test_execucoes_nao_sobrescrevem_resultados(self):
        primeira = self.comparar()
        antes = (primeira / 'pm_alex.wav').read_bytes()
        segunda = self.comparar()
        self.assertNotEqual(primeira, segunda)
        self.assertEqual((primeira / 'pm_alex.wav').read_bytes(), antes)

    def test_falta_modelo_nao_inicia_sessao(self):
        self.modelo.unlink()
        with self.assertRaises(FileNotFoundError):
            self.comparar()
        self.ort.InferenceSession.assert_not_called()

    def test_parametros_invalidos(self):
        for kwargs in [dict(texto=' '), dict(velocidade=0), dict(velocidade=float('nan')), dict(threads=8)]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.comparar(**kwargs)
        self.ort.InferenceSession.assert_not_called()

    def test_pacote_sem_pm_santa(self):
        self.motor.get_voices.return_value = ['pm_alex']
        with self.assertRaisesRegex(ValueError, 'pm_santa'):
            self.comparar()
        self.motor.create.assert_not_called()

    def test_falha_na_segunda_voz_registra_resultado_parcial(self):
        self.motor.create.side_effect = [(Array(), 24000), RuntimeError('falha no modelo')]
        with self.assertRaises(RuntimeError):
            self.comparar()
        registro = json.loads(next((self.pasta / 'saida').glob('*/comparacao.json')).read_text())
        self.assertEqual(registro['status'], 'falhou')
        self.assertEqual(len(registro['resultados']), 1)

    def test_audio_invalido_nao_vira_sucesso(self):
        self.motor.create.return_value = (Array(), 0)
        with self.assertRaisesRegex(ValueError, 'Áudio inválido'):
            self.comparar()
        self.sf.write.assert_not_called()

    def test_desempenho_alex_curta_e_maior(self):
        pasta = desempenho.testar(self.modelo, self.vozes, self.pasta / 'bench')
        chamadas = self.motor.create.call_args_list
        self.assertEqual(len(chamadas), 4)
        self.assertEqual([c.args[0] for c in chamadas], list(desempenho.TEXTOS.values()) * 2)
        self.assertTrue(all(c.kwargs['voice'] == 'pm_alex' for c in chamadas))
        self.assertEqual(self.ort.InferenceSession.call_args.kwargs['providers'], ['CPUExecutionProvider'])
        registro = json.loads((pasta / 'desempenho.json').read_text())
        self.assertEqual(registro['status'], 'concluido')
        self.assertEqual(len(list(pasta.glob('*.wav'))), 4)
        self.assertEqual([r['primeira_geracao'] for r in registro['resultados']], [True, False, False, False])
        for campo in ['importacao_segundos', 'carga_segundos', 'total_segundos']:
            self.assertGreaterEqual(registro[campo], 0)
        for resultado in registro['resultados']:
            for campo in ['geracao_segundos', 'gravacao_segundos', 'rtf']:
                self.assertGreaterEqual(resultado[campo], 0)

    def test_desempenho_falha_registra_parcial(self):
        self.motor.create.side_effect = [(Array(), 24000), RuntimeError('falha')]
        with self.assertRaises(RuntimeError):
            desempenho.testar(self.modelo, self.vozes, self.pasta / 'bench')
        registro = json.loads(next((self.pasta / 'bench').glob('*/desempenho.json')).read_text())
        self.assertEqual(registro['status'], 'falhou')
        self.assertEqual(len(registro['resultados']), 1)

    def test_desempenho_parametros_invalidos(self):
        for kwargs in [dict(threads=0), dict(repeticoes=0), dict(velocidade=float('nan'))]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                desempenho.testar(self.modelo, self.vozes, self.pasta / 'bench', **kwargs)
        self.ort.InferenceSession.assert_not_called()

    def test_desempenho_modelo_ausente(self):
        self.modelo.unlink()
        with self.assertRaises(FileNotFoundError):
            desempenho.testar(self.modelo, self.vozes, self.pasta / 'bench')
        self.ort.InferenceSession.assert_not_called()



class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pasta = Path(self.temp.name)
        p = patch.object(downloader, 'ARQUIVOS', [('teste.onnx', 4, 'https://example.org/teste.onnx')])
        p.start()
        self.addCleanup(p.stop)

    def test_download_verifica_tamanho_e_registra_hash(self):
        with patch.object(downloader.urllib.request, 'urlopen', return_value=io.BytesIO(b'test')):
            registros = downloader.baixar(self.pasta)
        self.assertEqual((self.pasta / 'teste.onnx').read_bytes(), b'test')
        self.assertEqual(registros[0]['sha256_local'], hashlib.sha256(b'test').hexdigest())

    def test_download_truncado_ou_maior_nao_publica_arquivo(self):
        for dados in [b'x', b'excesso']:
            with self.subTest(dados=dados), \
                 patch.object(downloader.urllib.request, 'urlopen', return_value=io.BytesIO(dados)), \
                 self.assertRaises(ValueError):
                downloader.baixar(self.pasta)
            self.assertEqual(list(self.pasta.iterdir()), [])

    def test_nao_sobrescreve_modelo(self):
        (self.pasta / 'teste.onnx').write_bytes(b'anterior')
        with patch.object(downloader.urllib.request, 'urlopen') as requisicao:
            with self.assertRaises(FileExistsError):
                downloader.baixar(self.pasta)
        requisicao.assert_not_called()
        self.assertEqual((self.pasta / 'teste.onnx').read_bytes(), b'anterior')


if __name__ == '__main__':
    unittest.main()
