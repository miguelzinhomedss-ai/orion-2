import sounddevice as sd
import soundfile as sf

ARQUIVO = "voz_teste.wav"
DURACAO = 5
TAXA = 44100

print("🎙️ Grave sua voz por 5 segundos...")
input("Pressione ENTER para começar...")

audio = sd.rec(
    int(DURACAO * TAXA),
    samplerate=TAXA,
    channels=1,
    dtype="float32"
)

sd.wait()
sf.write(ARQUIVO, audio, TAXA)

print(f"✅ Gravação salva em: {ARQUIVO}")