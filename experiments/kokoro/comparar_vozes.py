"""Comparação Kokoro isolada: sem Groq, GUI, reprodução ou downloads implícitos."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import tempfile
import time

VOZES = ('pm_alex', 'pm_santa')
FRASE = 'Boa noite. Todos os sistemas estão prontos. Estou à disposição para ajudar no que for necessário.'


def comparar(modelo, vozes, saida, texto=FRASE, velocidade=0.95, threads=2):
    """Carrega uma sessão CPU e grava a mesma frase em dois WAVs PCM de 16 bits.

    Cria um novo subdiretório por execução, sem sobrescrever resultados anteriores.
    Bibliotecas opcionais são importadas somente após validar os argumentos.
    """
    if not texto.strip():
        raise ValueError('A frase não pode estar vazia.')
    if not math.isfinite(velocidade) or not 0.5 <= velocidade <= 2.0:
        raise ValueError('A velocidade deve estar entre 0.5 e 2.0.')
    if not 1 <= threads <= 4:
        raise ValueError('Use de 1 a 4 threads; recomendado: 2 para o i3-9100F.')
    modelo, vozes, saida = Path(modelo), Path(vozes), Path(saida)
    for arquivo in (modelo, vozes):
        if not arquivo.is_file():
            raise FileNotFoundError(f'Arquivo local ausente: {arquivo}. Execute baixar_modelos.py primeiro.')
    try:
        import numpy as np
        import onnxruntime as ort
        import soundfile as sf
        from kokoro_onnx import Kokoro
    except ImportError as erro:
        raise RuntimeError('Instale experiments/kokoro/requirements.txt no ambiente separado.') from erro

    opcoes = ort.SessionOptions()
    opcoes.intra_op_num_threads = threads
    opcoes.inter_op_num_threads = 1
    opcoes.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    inicio = time.perf_counter()
    sessao = ort.InferenceSession(str(modelo), sess_options=opcoes,
                                 providers=['CPUExecutionProvider'])
    motor = Kokoro.from_session(sessao, str(vozes))
    disponiveis = motor.get_voices()
    faltantes = set(VOZES) - set(disponiveis)
    if faltantes:
        raise ValueError(f'Pacote sem as vozes necessárias: {sorted(faltantes)}')
    carga = time.perf_counter() - inicio
    saida.mkdir(parents=True, exist_ok=True)
    pasta = Path(tempfile.mkdtemp(prefix='comparacao-', dir=saida))
    relatorio = {
        'status': 'em_execucao', 'data_utc': datetime.now(timezone.utc).isoformat(),
        'texto': texto, 'velocidade': velocidade, 'idioma': 'pt-br',
        'provider': 'CPUExecutionProvider', 'threads': threads,
        'modelo': modelo.name, 'vozes': vozes.name,
        'carga_segundos': carga, 'resultados': [],
    }
    manifesto = pasta / 'comparacao.json'
    try:
        for voz in VOZES:
            inicio = time.perf_counter()
            amostras, taxa = motor.create(texto, voice=voz, speed=velocidade, lang='pt-br')
            duracao_geracao = time.perf_counter() - inicio
            amostras = np.asarray(amostras)
            if (amostras.ndim != 1 or amostras.size == 0 or
                    not np.isfinite(amostras).all() or not isinstance(taxa, int) or taxa <= 0):
                raise ValueError(f'Áudio inválido gerado por {voz}.')
            destino = pasta / f'{voz}.wav'
            # Modo exclusivo para nunca sobrescrever um arquivo já existente.
            with destino.open('xb') as arquivo:
                sf.write(arquivo, amostras, taxa, format='WAV', subtype='PCM_16')
            duracao_audio = len(amostras) / taxa
            relatorio['resultados'].append({
                'voz': voz, 'arquivo': destino.name, 'sample_rate': taxa,
                'geracao_segundos': duracao_geracao, 'audio_segundos': duracao_audio,
                'rtf': duracao_geracao / duracao_audio,
            })
        relatorio['status'] = 'concluido'
    except Exception:
        relatorio['status'] = 'falhou'
        raise
    finally:
        manifesto.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
    return pasta


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modelo', type=Path, required=True)
    parser.add_argument('--vozes', type=Path, required=True)
    parser.add_argument('--saida', type=Path, default=Path(__file__).parent / 'resultados')
    parser.add_argument('--texto', default=FRASE)
    parser.add_argument('--velocidade', type=float, default=0.95)
    parser.add_argument('--threads', type=int, default=2)
    args = parser.parse_args(argv)
    try:
        pasta = comparar(args.modelo, args.vozes, args.saida, args.texto,
                         args.velocidade, args.threads)
    except Exception as erro:
        parser.exit(1, f'Falha no teste Kokoro: {erro}\n')
    print(f'Comparação concluída: {pasta.resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
