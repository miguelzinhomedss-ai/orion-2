"""Mede pm_alex por CPU: carga, geração e gravação de frases curta e longa."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import statistics
import tempfile
import time

TEXTOS = {
    'curta': 'Boa noite. Estou pronto para ajudar.',
    'maior': (
        'Boa noite. Analisei as informações disponíveis e preparei um resumo para você. '
        'Podemos começar pelas tarefas mais importantes e depois organizar os próximos passos. '
        'Se surgir alguma dúvida, explicarei cada etapa com calma e clareza. '
        'Meu objetivo é ajudar você a tomar decisões com segurança, sem perder tempo com detalhes desnecessários. '
        'Quando estiver pronto, diga qual assunto deseja explorar primeiro.'
    ),
}


def testar(modelo, vozes, saida, threads=2, repeticoes=2, velocidade=0.95):
    if not 1 <= threads <= 4 or not 1 <= repeticoes <= 10:
        raise ValueError('Use 1 a 4 threads e 1 a 10 repetições.')
    if not math.isfinite(velocidade) or not 0.5 <= velocidade <= 2:
        raise ValueError('Velocidade deve estar entre 0.5 e 2.0.')
    modelo, vozes = Path(modelo), Path(vozes)
    for arquivo in (modelo, vozes):
        if not arquivo.is_file():
            raise FileNotFoundError(f'Arquivo local ausente: {arquivo}. Execute baixar_modelos.py primeiro.')
    total_inicio = time.perf_counter()
    inicio = time.perf_counter()
    try:
        import numpy as np
        import onnxruntime as ort
        import soundfile as sf
        from kokoro_onnx import Kokoro
    except ImportError as erro:
        raise RuntimeError('Instale os requirements do experimento no ambiente separado.') from erro
    importacao = time.perf_counter() - inicio
    opcoes = ort.SessionOptions()
    opcoes.intra_op_num_threads = threads
    opcoes.inter_op_num_threads = 1
    opcoes.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    inicio = time.perf_counter()
    sessao = ort.InferenceSession(str(modelo), sess_options=opcoes,
                                 providers=['CPUExecutionProvider'])
    motor = Kokoro.from_session(sessao, str(vozes))
    if 'pm_alex' not in motor.get_voices():
        raise ValueError('O pacote local não contém pm_alex.')
    carga = time.perf_counter() - inicio
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    pasta = Path(tempfile.mkdtemp(prefix='desempenho-alex-', dir=saida))
    relatorio = {
        'status': 'em_execucao', 'data_utc': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(), 'sistema': platform.platform(),
        'processador': platform.processor(), 'voz': 'pm_alex', 'idioma': 'pt-br',
        'provider': 'CPUExecutionProvider', 'threads': threads,
        'velocidade': velocidade, 'repeticoes': repeticoes,
        'modelo': modelo.name, 'arquivo_vozes': vozes.name,
        'importacao_segundos': importacao, 'carga_segundos': carga,
        'textos': TEXTOS, 'resultados': [],
    }
    print(f'Bibliotecas: {importacao:.2f} s | Carga do modelo/vozes: {carga:.2f} s', flush=True)
    print('CPU, pm_alex. Sem aquecimento oculto: a primeira geração é a frase curta.', flush=True)
    print('Frase   Rodada   Gerar(s)   Gravar(s)   Áudio(s)   RTF', flush=True)
    try:
        for rodada in range(1, repeticoes + 1):
            for nome, texto in TEXTOS.items():
                inicio = time.perf_counter()
                audio, taxa = motor.create(texto, voice='pm_alex', speed=velocidade, lang='pt-br')
                geracao = time.perf_counter() - inicio
                audio = np.asarray(audio)
                if (audio.ndim != 1 or audio.size == 0 or not np.isfinite(audio).all()
                        or not isinstance(taxa, int) or taxa <= 0):
                    raise ValueError(f'Áudio inválido para a frase {nome}.')
                duracao = len(audio) / taxa
                arquivo = pasta / f'pm_alex_{nome}_{rodada:02d}.wav'
                inicio = time.perf_counter()
                with arquivo.open('xb') as stream:
                    sf.write(stream, audio, taxa, format='WAV', subtype='PCM_16')
                gravacao = time.perf_counter() - inicio
                registro = {
                    'frase': nome, 'rodada': rodada, 'primeira_geracao': not relatorio['resultados'],
                    'geracao_segundos': geracao, 'gravacao_segundos': gravacao,
                    'audio_segundos': duracao, 'rtf': geracao / duracao,
                    'arquivo': arquivo.name, 'sample_rate': taxa,
                }
                relatorio['resultados'].append(registro)
                print(f'{nome:<7} {rodada:>6} {geracao:>10.2f} {gravacao:>11.3f} '
                      f'{duracao:>10.2f} {geracao / duracao:>7.2f}', flush=True)
        relatorio['medianas_geracao_segundos'] = {
            nome: statistics.median(r['geracao_segundos'] for r in relatorio['resultados']
                                    if r['frase'] == nome) for nome in TEXTOS
        }
        relatorio['status'] = 'concluido'
    except Exception:
        relatorio['status'] = 'falhou'
        raise
    finally:
        relatorio['total_segundos'] = time.perf_counter() - total_inicio
        (pasta / 'desempenho.json').write_text(
            json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Resultados e WAVs: {pasta.resolve()}', flush=True)
    return pasta


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo', type=Path, required=True)
    parser.add_argument('--vozes', type=Path, required=True)
    parser.add_argument('--saida', type=Path, default=Path(__file__).parent / 'resultados')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--repeticoes', type=int, default=2)
    parser.add_argument('--velocidade', type=float, default=0.95)
    args = parser.parse_args(argv)
    try:
        testar(args.modelo, args.vozes, args.saida, args.threads, args.repeticoes, args.velocidade)
    except Exception as erro:
        parser.exit(1, f'Falha no teste de desempenho: {erro}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
