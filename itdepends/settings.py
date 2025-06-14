import os
import dotenv
import pathlib

# Load environment variables from .env file
dotenv.load_dotenv(pathlib.Path(__file__).parent.parent / ".env")


def get_env(key: str, default: str = None) -> str:
    """Get environment variable with optional default."""
    return os.getenv(key, default)


# API Configuration
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
EVALUATION_MODEL = get_env("EVALUATION_MODEL", "gpt-4o")
TRANSCRIPTION_MODEL = get_env("TRANSCRIPTION_MODEL", "whisper-1")
TRANSCRIPTION_SESSIONS_URL = "https://api.openai.com/v1/realtime/transcription_sessions"
REALTIME_WS_URL = "wss://api.openai.com/v1/realtime"