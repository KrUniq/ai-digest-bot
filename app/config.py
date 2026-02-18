import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

MODEL_TRAVEL = os.getenv("MODEL_TRAVEL", "llama3:latest")
MODEL_FAST = os.getenv("MODEL_FAST", "llama3.2:3b")

DEFAULT_MODE = os.getenv("DEFAULT_MODE", "travel")
