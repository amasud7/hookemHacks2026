from google import genai
from google.genai import types
import numpy as np

from src.config import GOOGLE_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMS

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def normalize_l2(vec: list[float]) -> list[float]:
    """L2-normalize a vector. Required for 768-dim Gemini embeddings (only 3072 are auto-normalized)."""
    arr = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm == 0:
        return arr.tolist()
    return (arr / norm).tolist()


def embed_text(text: str) -> list[float]:
    """Embed text content (caption, transcript, etc.) as a search document."""
    result = _get_client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=f"task: search result | {text}",
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMS),
    )
    return normalize_l2(result.embeddings[0].values)


def embed_video(video_bytes: bytes, mime_type: str = "video/mp4") -> list[float]:
    """Embed video content. Gemini samples 32 frames, max 120s. Does NOT process audio track."""
    result = _get_client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=types.Part.from_bytes(data=video_bytes, mime_type=mime_type),
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMS),
    )
    return normalize_l2(result.embeddings[0].values)


def embed_audio(audio_bytes: bytes, mime_type: str = "audio/mpeg") -> list[float]:
    """Embed audio content. Max 80s. Use for audio extracted from video via ffmpeg."""
    result = _get_client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMS),
    )
    return normalize_l2(result.embeddings[0].values)



def embed_query(query_text: str) -> list[float]:
    """Embed a user search query. Uses 'task: search query' prefix for retrieval asymmetry."""
    result = _get_client().models.embed_content(
        model=EMBEDDING_MODEL,
        contents=f"task: search query | {query_text}",
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMS),
    )
    return normalize_l2(result.embeddings[0].values)
