import io

from groq import Groq

from src.config import GROQ_API_KEY

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def transcribe_audio(audio_bytes: bytes, suffix: str = ".webm") -> str:
    """Transcribe audio bytes to text using Groq Whisper API.

    Returns the transcribed text, or empty string on failure.
    """
    try:
        # Map suffix to a filename Groq can accept
        filename = f"audio{suffix}"
        transcription = _get_client().audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=(filename, io.BytesIO(audio_bytes)),
        )
        return transcription.text.strip()
    except Exception as e:
        print(f"Groq transcription error: {e}")
        return ""
