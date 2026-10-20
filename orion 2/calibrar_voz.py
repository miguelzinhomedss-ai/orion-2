from speechbrain.inference.speaker import SpeakerRecognition
from speechbrain.utils.fetching import LocalStrategy

print("Carregando modelo...")
verificador = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_model",
    local_strategy=LocalStrategy.COPY
)

def score(arquivo1, arquivo2):
    resultado = verificador.verify_batch(
        verificador.load_audio(arquivo1),
        verificador.load_audio(arquivo2)
    )
    return float(resultado[0].item())

print("Modelo carregado!\n")

referencia = "orion_voz_miguel.wav"

print("=== TESTE COM SUA VOZ ===")

meus_scores = []

for i in range(3):
    print(f"\nGravação {i + 1}/3")
    input("Pressione ENTER e fale por 5 segundos...")

    import sounddevice as sd
    import soundfile as sf

    audio = sd.rec(
        5 * 44100,
        samplerate=44100,
        channels=1,
        dtype="float32"
    )
    sd.wait()

    arquivo = f"minha_voz_{i + 1}.wav"
    sf.write(arquivo, audio, 44100)

    valor = score(referencia, arquivo)
    meus_scores.append(valor)

    print(f"Score: {valor:.4f}")

print("\n=== RESULTADO ===")
print("Seus scores:")

for valor in meus_scores:
    print(f"- {valor:.4f}")

print(f"\nMenor score seu: {min(meus_scores):.4f}")
print(f"Maior score seu: {max(meus_scores):.4f}")
print(f"Média: {sum(meus_scores) / len(meus_scores):.4f}")