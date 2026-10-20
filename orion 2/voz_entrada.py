"""Captura opcional de microfone, compatível com a fila de eventos da interface."""
import threading


class ReconhecedorVoz:
    def __init__(self, indice_microfone=None):
        # Nenhum acesso a hardware ou importação de PyAudio durante a inicialização.
        self.indice_microfone = indice_microfone

    def ouvir(self, cancelamento=None):
        """Retorna texto pt-BR ou None para silêncio/cancelamento/fala ininteligível.

        Falhas de dispositivo/rede são propagadas para a interface desativar voz.
        A captura é limitada a 1s de espera e 5s de fala; a rede tem timeout de 5s.
        O Google recebe áudio somente quando o usuário ativa o modo de voz.
        """
        cancelamento = cancelamento if cancelamento is not None else threading.Event()
        if cancelamento.is_set():
            return None
        try:
            import speech_recognition as sr
        except ImportError as erro:
            raise RuntimeError('Instale SpeechRecognition e PyAudio para usar o microfone.') from erro
        reconhecedor = sr.Recognizer()
        reconhecedor.operation_timeout = 5
        try:
            with sr.Microphone(device_index=self.indice_microfone) as fonte:
                if cancelamento.is_set():
                    return None
                audio = reconhecedor.listen(fonte, timeout=1, phrase_time_limit=5)
            if cancelamento.is_set():
                return None
            texto = reconhecedor.recognize_google(audio, language='pt-BR')
            return None if cancelamento.is_set() else texto
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None
        except Exception as erro:
            raise RuntimeError('Microfone ou serviço de reconhecimento indisponível.') from erro
