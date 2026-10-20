"""Síntese local CPU opcional, com sessão persistente e trechos curtos."""
from io import BytesIO
from pathlib import Path
import re
import textwrap
import threading

import config

_motor = None
_chave = None
_lock = threading.Lock()


def dividir_texto(texto, limite=160, primeiro=80):
    """Prefere fim de frase/oração e mantém palavras inteiras nos trechos."""
    if limite < 20 or primeiro < 20:
        raise ValueError('Os limites dos trechos devem ser pelo menos 20 caracteres.')
    partes = re.split(r'(?<=[.!?;:])\s+|\n+', texto.strip())
    resultado = []
    for parte in partes:
        parte = ' '.join(parte.split())
        while parte:
            alvo = primeiro if not resultado else limite
            if len(parte) <= alvo:
                resultado.append(parte)
                break
            # Prefere vírgula a uma quebra arbitrária no meio de uma oração.
            virgula = parte.rfind(', ', 20, alvo)
            if virgula >= 0:
                trecho = parte[:virgula + 1]
            else:
                trecho = textwrap.wrap(parte, width=alvo, break_long_words=False,
                                       break_on_hyphens=False)[0]
            resultado.append(trecho)
            parte = parte[len(trecho):].strip()
    return resultado


def _carregar():
    global _motor, _chave
    modelo = Path(config.KOKORO_MODEL).expanduser().resolve()
    vozes = Path(config.KOKORO_VOICES).expanduser().resolve()
    threads = int(config.KOKORO_THREADS)
    if not 1 <= threads <= 4:
        raise ValueError('Kokoro: use 1 a 4 threads.')
    chave = (str(modelo), str(vozes), threads)
    if _motor is not None and _chave == chave:
        return _motor
    for arquivo in (modelo, vozes):
        if not arquivo.is_file():
            raise FileNotFoundError(f'Modelo Kokoro local ausente: {arquivo}')
    import onnxruntime as ort
    from kokoro_onnx import Kokoro
    opcoes = ort.SessionOptions()
    opcoes.intra_op_num_threads = threads
    opcoes.inter_op_num_threads = 1
    opcoes.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    # Mantém o modelo em RAM, mas evita threads ocupadas quando está ocioso.
    opcoes.add_session_config_entry('session.intra_op.allow_spinning', '0')
    opcoes.add_session_config_entry('session.inter_op.allow_spinning', '0')
    sessao = ort.InferenceSession(str(modelo), sess_options=opcoes,
                                 providers=['CPUExecutionProvider'])
    motor = Kokoro.from_session(sessao, str(vozes))
    _motor, _chave = motor, chave
    return motor


def gerar_audio(texto):
    """Carrega na primeira chamada; reutiliza a sessão nas seguintes, sem download."""
    with _lock:
        import numpy as np
        import soundfile as sf
        motor = _carregar()
        velocidade = float(config.KOKORO_SPEED)
        if not 0.5 <= velocidade <= 2.0:
            raise ValueError('Velocidade Kokoro deve estar entre 0.5 e 2.0.')
        audio, taxa = motor.create(texto, voice=config.KOKORO_VOICE,
                                  speed=velocidade, lang='pt-br')
        audio = np.asarray(audio)
        if (audio.ndim != 1 or audio.size == 0 or not np.isfinite(audio).all()
                or not isinstance(taxa, int) or taxa <= 0):
            raise ValueError('Kokoro retornou áudio inválido.')
        memoria = BytesIO()
        sf.write(memoria, audio, taxa, format='WAV', subtype='PCM_16')
        memoria.seek(0)
        return memoria
