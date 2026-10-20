"""Voz neural brasileira com fallback local; falhas preservam o chat."""
import asyncio
import logging
from pathlib import Path
import tempfile
import time

import config
import threading
import unicodedata

_log = logging.getLogger(__name__)
_lock = threading.Lock()


def _normalizar(valor):
    if isinstance(valor, bytes):
        valor = valor.decode('utf-8', errors='ignore')
    return ''.join(c for c in unicodedata.normalize('NFD', str(valor).lower())
                   if not unicodedata.combining(c))


def _escolher_voz(vozes):
    portugues = []
    for voz in vozes:
        dados = _normalizar(' '.join([str(voz.id), str(voz.name)]))
        idiomas = ' '.join(_normalizar(v) for v in (voz.languages or []))
        if any(tag in idiomas + ' ' + dados for tag in
               ('pt-br', 'pt_br', 'portugu', 'brazil', 'brasil')) or idiomas.strip() == 'pt':
            masculino = _normalizar(getattr(voz, 'gender', '') or '') == 'male'
            masculino |= any(nome in dados for nome in ('daniel', 'antonio', 'ricardo', 'paulo'))
            brasileiro = any(tag in idiomas + ' ' + dados for tag in ('pt-br', 'pt_br', 'brazil', 'brasil'))
            portugues.append(((brasileiro, masculino), voz.id))
    return max(portugues, key=lambda item: item[0])[1] if portugues else None


def _falar_offline(texto):
    """Fala de forma síncrona na thread de trabalho; retorna sucesso ou False.

    Usa as vozes SAPI5 instaladas no Windows, sem enviar texto à nuvem.
    O motor é criado e destruído na mesma thread (necessário para COM/SAPI).
    """
    if not isinstance(texto, str) or not texto.strip():
        return False
    motor = None
    try:
        import pyttsx3
        motor = pyttsx3.init()
        voz = config.TTS_OFFLINE_VOICE or _escolher_voz(motor.getProperty('voices'))
        if voz is None:
            _log.warning('Nenhuma voz portuguesa instalada; resposta disponível no chat.')
            return False
        motor.setProperty('voice', voz)
        motor.setProperty('rate', config.TTS_OFFLINE_RATE)
        motor.say(texto)
        motor.runAndWait()
        return True
    except Exception:
        _log.warning('Saída de voz indisponível; resposta disponível no chat.')
        return False
    finally:
        if motor is not None:
            try:
                motor.stop()
            except Exception:
                pass


async def _gerar_online(texto, arquivo):
    import edge_tts
    comunicador = edge_tts.Communicate(
        texto, voice=config.TTS_VOICE, rate=config.TTS_RATE,
        pitch=config.TTS_PITCH, connect_timeout=5, receive_timeout=10,
    )
    await asyncio.wait_for(comunicador.save(str(arquivo)), timeout=config.TTS_TIMEOUT)


def _reproduzir(arquivo):
    # Toda a reprodução (inclusive offline) é protegida por _lock em falar().
    from pygame import mixer
    try:
        mixer.init()
        mixer.music.load(str(arquivo))
        mixer.music.play()
        inicio = time.monotonic()
        while mixer.music.get_busy():
            if time.monotonic() - inicio > config.TTS_PLAYBACK_TIMEOUT:
                raise TimeoutError('Reprodução excedeu o limite de tempo.')
            time.sleep(0.02)
    finally:
        # Libera o MP3 antes de remover o diretório temporário no Windows.
        try:
            if mixer.get_init():
                mixer.music.stop()
                mixer.music.unload()
        finally:
            mixer.quit()


def _falar_online(texto):
    with tempfile.TemporaryDirectory(prefix='orion-voz-') as pasta:
        arquivo = Path(pasta) / 'fala.mp3'
        asyncio.run(_gerar_online(texto, arquivo))
        _reproduzir(arquivo)


def falar(texto):
    """Executar na thread de trabalho, como já faz OrionInterface.

    Retorna após a reprodução, evitando reabrir o microfone enquanto fala.
    Serializa chamadas concorrentes e tenta SAPI/pyttsx3 se o online falhar.
    """
    if not isinstance(texto, str) or not texto.strip():
        return False
    with _lock:
        if config.TTS_BACKEND.lower() != 'offline':
            try:
                _falar_online(texto)
                return True
            except Exception:
                _log.warning('Voz online indisponível; tentando síntese offline.')
        return _falar_offline(texto)
