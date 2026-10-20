"""Voz neural brasileira com fallback local; falhas preservam o chat."""
from contextlib import contextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import logging
from pathlib import Path
import tempfile
import time

import config
import threading
import unicodedata

_log = logging.getLogger(__name__)
_lock = threading.Lock()
_estado_lock = threading.Lock()
_contexto = threading.local()
_cancelamento_atual = None


class _FalaCancelada(Exception):
    pass


def _verificar_cancelamento():
    evento = getattr(_contexto, 'cancelamento', None)
    if evento is not None and evento.is_set():
        raise _FalaCancelada()


@contextmanager
def contexto_fala(evento=None):
    """Propaga cancelamento de uma resposta, inclusive antes de falar começar."""
    anterior = getattr(_contexto, 'cancelamento', None)
    _contexto.cancelamento = evento if evento is not None else threading.Event()
    try:
        yield
    finally:
        if anterior is None:
            del _contexto.cancelamento
        else:
            _contexto.cancelamento = anterior


def cancelar_fala():
    """Pode ser chamada pelo Tk: apenas sinaliza, sem acessar dispositivos."""
    with _estado_lock:
        if _cancelamento_atual is not None:
            _cancelamento_atual.set()



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
    loop_iniciado = False
    try:
        _verificar_cancelamento()
        import pyttsx3
        motor = pyttsx3.init()
        voz = config.TTS_OFFLINE_VOICE or _escolher_voz(motor.getProperty('voices'))
        if voz is None:
            _log.warning('Nenhuma voz portuguesa instalada; resposta disponível no chat.')
            return False
        motor.setProperty('voice', voz)
        motor.setProperty('rate', config.TTS_OFFLINE_RATE)
        motor.say(texto)
        motor.startLoop(False)
        loop_iniciado = True
        motor.iterate()
        inicio = time.monotonic()
        while motor.isBusy():
            _verificar_cancelamento()
            if time.monotonic() - inicio > config.TTS_PLAYBACK_TIMEOUT:
                raise TimeoutError('Síntese offline excedeu o limite de tempo.')
            motor.iterate()
            time.sleep(0.02)
        _verificar_cancelamento()
        return True
    except _FalaCancelada:
        raise
    except Exception:
        _log.warning('Saída de voz indisponível; resposta disponível no chat.')
        return False
    finally:
        if motor is not None:
            try:
                motor.stop()
            except Exception:
                pass
            if loop_iniciado:
                try:
                    motor.endLoop()
                except Exception:
                    pass


async def _gerar_online(texto, arquivo):
    import edge_tts
    comunicador = edge_tts.Communicate(
        texto, voice=config.TTS_VOICE, rate=config.TTS_RATE,
        pitch=config.TTS_PITCH, connect_timeout=5, receive_timeout=10,
    )
    tarefa = asyncio.create_task(comunicador.save(str(arquivo)))
    limite = time.monotonic() + config.TTS_TIMEOUT
    try:
        while True:
            _verificar_cancelamento()
            restante = limite - time.monotonic()
            if restante <= 0:
                raise TimeoutError('Geração online excedeu o limite de tempo.')
            prontos, _ = await asyncio.wait({tarefa}, timeout=min(0.05, restante))
            if prontos:
                await tarefa
                _verificar_cancelamento()
                return
    finally:
        if not tarefa.done():
            tarefa.cancel()
        try:
            await tarefa
        except (asyncio.CancelledError, Exception):
            pass


def _reproduzir(arquivo):
    # Toda a reprodução (inclusive offline) é protegida por _lock em falar().
    from pygame import mixer
    try:
        _verificar_cancelamento()
        mixer.init()
        mixer.music.load(arquivo if hasattr(arquivo, 'read') else str(arquivo))
        _verificar_cancelamento()
        mixer.music.play()
        if hasattr(_contexto, 'inicio') and not _contexto.primeira_reproducao:
            _contexto.primeira_reproducao = True
            _log.info('TTS: primeira reprodução iniciada em %.3f s desde falar().',
                      time.perf_counter() - _contexto.inicio)
        inicio = time.monotonic()
        while mixer.music.get_busy():
            _verificar_cancelamento()
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
    _verificar_cancelamento()
    with tempfile.TemporaryDirectory(prefix='orion-voz-') as pasta:
        arquivo = Path(pasta) / 'fala.mp3'
        asyncio.run(_gerar_online(texto, arquivo))
        _reproduzir(arquivo)


def _falar_alternativas(texto):
    _verificar_cancelamento()
    try:
        _falar_online(texto)
        return True
    except _FalaCancelada:
        raise
    except Exception:
        _log.warning('Voz online indisponível; tentando síntese offline.')
        return _falar_offline(texto)


def _falar_kokoro(texto):
    from voz_kokoro import dividir_texto, gerar_audio
    trechos = dividir_texto(texto, config.KOKORO_CHUNK_CHARS, config.KOKORO_FIRST_CHARS)
    futuros = []
    restante = None
    evento = getattr(_contexto, 'cancelamento', None)
    inicio = time.perf_counter()
    def gerar(trecho):
        if evento is not None and evento.is_set():
            raise _FalaCancelada()
        audio = gerar_audio(trecho)
        if evento is not None and evento.is_set():
            audio.close()
            raise _FalaCancelada()
        return audio
    try:
        # Uma geração antecipada, áudio em RAM; sem escrever trechos no HD.
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix='kokoro-geracao') as produtor:
            futuro = produtor.submit(gerar, trechos[0])
            futuros.append(futuro)
            for indice, trecho in enumerate(trechos):
                try:
                    while True:
                        _verificar_cancelamento()
                        try:
                            audio = futuro.result(timeout=0.05)
                            break
                        except FutureTimeout:
                            if futuro.done():
                                raise
                    _verificar_cancelamento()
                    if indice + 1 < len(trechos):
                        futuro = produtor.submit(gerar, trechos[indice + 1])
                        futuros.append(futuro)
                    try:
                        if indice == 0:
                            _log.info('Kokoro: primeiro trecho pronto em %.3f s (antes de iniciar o player).',
                                      time.perf_counter() - inicio)
                        _reproduzir(audio)
                    finally:
                        audio.close()
                except _FalaCancelada:
                    futuro.cancel()
                    raise
                except Exception:
                    _verificar_cancelamento()
                    futuro.cancel()
                    restante = ' '.join(trechos[indice:])
                    break
    finally:
        # O executor já encerrou: libera também um trecho antecipado não usado.
        for futuro in futuros:
            if futuro.done() and not futuro.cancelled():
                try:
                    futuro.result().close()
                except Exception:
                    pass
    if restante is not None:
        _log.warning('Kokoro indisponível; tentando voz alternativa para o texto restante.')
        # Um trecho parcialmente reproduzido pode ser repetido; os concluídos não.
        return _falar_alternativas(restante)
    return True


def falar(texto):
    """Thread de trabalho, áudio serializado, cancelamento cooperativo."""
    global _cancelamento_atual
    if not isinstance(texto, str) or not texto.strip():
        return False
    with _lock:
        anterior = getattr(_contexto, 'cancelamento', None)
        evento = anterior if anterior is not None else threading.Event()
        with _estado_lock:
            _cancelamento_atual = evento
        _contexto.cancelamento = evento
        _contexto.inicio = time.perf_counter()
        _contexto.primeira_reproducao = False
        try:
            _verificar_cancelamento()
            backend = config.TTS_BACKEND.lower()
            if backend in ('offline', 'pyttsx3'):
                return _falar_offline(texto)
            if backend == 'kokoro':
                try:
                    return _falar_kokoro(texto)
                except _FalaCancelada:
                    raise
                except Exception:
                    _log.warning('Kokoro indisponível; tentando voz alternativa.')
            return _falar_alternativas(texto)
        except _FalaCancelada:
            return False
        finally:
            with _estado_lock:
                _cancelamento_atual = None
            if anterior is None:
                del _contexto.cancelamento
            else:
                _contexto.cancelamento = anterior
            del _contexto.inicio
            del _contexto.primeira_reproducao
