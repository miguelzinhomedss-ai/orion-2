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

# Síntese principal online; use ORION_TTS_BACKEND=offline para não enviar texto.
TTS_BACKEND = os.getenv("ORION_TTS_BACKEND", "edge")
TTS_VOICE = os.getenv("ORION_TTS_VOICE", "pt-BR-AntonioNeural")
TTS_RATE = os.getenv("ORION_TTS_RATE", "-8%")
TTS_PITCH = os.getenv("ORION_TTS_PITCH", "-5Hz")
TTS_TIMEOUT = 20  # Limite total para gerar uma resposta de voz online.
TTS_PLAYBACK_TIMEOUT = 180
TTS_OFFLINE_VOICE = os.getenv("ORION_TTS_OFFLINE_VOICE", "")
TTS_OFFLINE_RATE = 165  # Palavras por minuto; SAPI não oferece pitch portátil.
