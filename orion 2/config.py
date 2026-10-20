# ============================================================
# ORION 2.0 — CONFIGURAÇÕES
# ============================================================

import os
from dotenv import load_dotenv

# Carrega o arquivo .env
load_dotenv()


# ============================================================
# API
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


# ============================================================
# INTELIGÊNCIA
# ============================================================

MODEL = "openai/gpt-oss-120b"

MAX_HISTORY = 30


# ============================================================
# VOZ
# ============================================================

VOICE_ID = "dTm5RYZC4u"

VOICE_STABILITY = 0.45
VOICE_SIMILARITY = 0.75
VOICE_STYLE = 0.35


# ============================================================
# INTERFACE
# ============================================================

APP_NAME = "ORION"

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700

BG_COLOR = "#050a12"
CYAN = "#00d9ff"
GREEN = "#00ff9d"
WHITE = "#e8faff"
GRAY = "#78909c"
DARK_GRAY = "#0b141e"


# ============================================================
# MEMÓRIA
# ============================================================

MEMORY_FILE = "orion_memoria.json"
TASKS_FILE = "orion_tarefas.json"


# ============================================================
# SISTEMA
# ============================================================

WAKE_WORD = "orion"

DEBUG = True

# Kokoro principal; edge e offline permanecem como alternativas.
TTS_BACKEND = os.getenv("ORION_TTS_BACKEND", "kokoro")
TTS_VOICE = os.getenv("ORION_TTS_VOICE", "pt-BR-AntonioNeural")
TTS_RATE = os.getenv("ORION_TTS_RATE", "-8%")
TTS_PITCH = os.getenv("ORION_TTS_PITCH", "-5Hz")
TTS_TIMEOUT = 20  # Limite total para gerar uma resposta de voz online.
TTS_PLAYBACK_TIMEOUT = 180
TTS_OFFLINE_VOICE = os.getenv("ORION_TTS_OFFLINE_VOICE", "")
TTS_OFFLINE_RATE = 165  # Palavras por minuto; SAPI não oferece pitch portátil.


# Kokoro opcional: arquivos locais, CPU, carregamento preguiçoso e persistente.
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOKORO_MODEL = os.getenv("ORION_KOKORO_MODEL", os.path.join(
    _PROJECT_DIR, "experiments", "kokoro", "modelos", "kokoro-v1.0.int8.onnx"))
KOKORO_VOICES = os.getenv("ORION_KOKORO_VOICES", os.path.join(
    _PROJECT_DIR, "experiments", "kokoro", "modelos", "voices-v1.0.bin"))
KOKORO_VOICE = os.getenv("ORION_KOKORO_VOICE", "pm_alex")
KOKORO_THREADS = os.getenv("ORION_KOKORO_THREADS", "2")
KOKORO_SPEED = os.getenv("ORION_KOKORO_SPEED", "0.95")
KOKORO_CHUNK_CHARS = 160
KOKORO_FIRST_CHARS = 80
