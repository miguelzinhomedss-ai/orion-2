# ============================================================
# ORION 2.0 — COMANDOS DO SISTEMA
# ============================================================

import os
import subprocess
import webbrowser
import datetime
import platform
import psutil


# ============================================================
# SITES
# ============================================================

def abrir_site(site):
    sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "spotify": "https://open.spotify.com",
        "github": "https://github.com",
        "gmail": "https://mail.google.com",
        "instagram": "https://www.instagram.com",
    }

    url = sites.get(site.lower())

    if not url:
        return False

    webbrowser.open(url)
    return True


# ============================================================
# PROGRAMAS
# ============================================================

def abrir_programa(programa):

    programas = {
    "bloco de notas": "notepad.exe",
    "notepad": "notepad.exe",
    "steam": "steam.exe",
}
def abrir_spotify():

    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "spotify:"],
            shell=False
        )
        return True

    except Exception as erro:
        print(f"[SPOTIFY] Erro: {erro}")
        return False
    caminho = programas.get(programa.lower())

    if not caminho:
        return False

    try:
        subprocess.Popen(caminho)
        return True

    except Exception as erro:
        print(f"[COMANDO] Erro: {erro}")
        return False


# ============================================================
# DATA E HORA
# ============================================================

def obter_hora():

    agora = datetime.datetime.now()

    return agora.strftime("%H:%M")


def obter_data():

    agora = datetime.datetime.now()

    return agora.strftime("%d/%m/%Y")


# ============================================================
# STATUS DO PC
# ============================================================

def status_pc():

    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()

    ram_usada = ram.percent

    disco = psutil.disk_usage("/")

    return {
        "cpu": cpu,
        "ram": ram_usada,
        "disco": disco.percent,
        "sistema": platform.system(),
        "versao": platform.release(),
    }


# ============================================================
# RESUMO DO STATUS
# ============================================================

def resumo_status():

    status = status_pc()

    return (
        f"CPU em {status['cpu']:.0f}%. "
        f"Memória RAM em {status['ram']:.0f}%. "
        f"Disco em {status['disco']:.0f}%. "
        f"Sistema {status['sistema']} "
        f"{status['versao']}."
    )


# ============================================================
# DESLIGAMENTO
# ============================================================

def desligar_pc(tempo=3600):

    try:

        subprocess.run(
            ["shutdown", "-s", "-t", str(tempo)],
            check=True
        )

        return True

    except Exception as erro:

        print(f"[COMANDO] Erro ao desligar: {erro}")

        return False


def cancelar_desligamento():

    try:

        subprocess.run(
            ["shutdown", "-a"],
            check=True
        )

        return True

    except Exception as erro:

        print(f"[COMANDO] Erro ao cancelar: {erro}")

        return False


# ============================================================
# VOLUME
# ============================================================

def definir_volume(valor):

    try:

        from pycaw.pycaw import AudioUtilities

        dispositivos = AudioUtilities.GetSpeakers()

        volume = dispositivos.EndpointVolume

        valor = max(0, min(100, int(valor)))

        volume.SetMasterVolumeLevelScalar(
            valor / 100,
            None
        )

        return True

    except Exception as erro:

        print(f"[VOLUME] Erro: {erro}")

        return False


def obter_volume():

    try:

        from pycaw.pycaw import AudioUtilities

        dispositivos = AudioUtilities.GetSpeakers()

        volume = dispositivos.EndpointVolume

        atual = volume.GetMasterVolumeLevelScalar()

        return round(atual * 100)

    except Exception as erro:

        print(f"[VOLUME] Erro: {erro}")

        return None


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    print("ORION — TESTE DE COMANDOS")
    print()
    print("Hora:", obter_hora())
    print("Data:", obter_data())
    print("Status:", resumo_status())
    print("Volume:", obter_volume())