import tempfile
from pathlib import Path

import whisper

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("small")
    return _model


def transcribe_audio(audio_bytes: bytes, suffix: str = ".webm") -> str:
    """Transcribe audio bytes to text using local Whisper model.

    Returns the transcribed text, or empty string on failure.
    Model loads once (~2s first call), transcription ~1-2s per short clip on CPU.
    """
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    try:
        result = _get_model().transcribe(tmp_path)
        return result["text"].strip()
    except Exception:
        return ""
    finally:
        Path(tmp_path).unlink(missing_ok=True)
