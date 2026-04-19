"""Generate text descriptions of video/image content using Gemini vision.

No ffmpeg dependency — sends video bytes directly to Gemini which samples frames natively.
Falls back to Claude for image description.
"""

import base64
import json

from google import genai
from google.genai import types

from src.config import GOOGLE_API_KEY

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def describe_video(video_bytes: bytes, suffix: str = ".mp4") -> str:
    """Generate a text description of video content using Gemini vision.

    Sends raw video bytes — Gemini samples 32 frames automatically.
    Returns a concise description focused on actions and events.
    Returns empty string on failure.
    """
    mime_map = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}
    mime_type = mime_map.get(suffix.lower(), "video/mp4")

    try:
        response = _get_client().models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=video_bytes, mime_type=mime_type),
                (
                    "These are frames from a short-form video (TikTok/Instagram Reel). "
                    "Describe what is HAPPENING in this video in 1-2 sentences. "
                    "Focus on ACTIONS, MOTION, EVENTS, and SUBJECTS — not colors, lighting, or image quality. "
                    "Be specific and concise."
                ),
            ],
        )
        return response.text.strip()
    except Exception as e:
        print(f"  Video description failed: {e}")
        return ""


def describe_image(image_bytes: bytes) -> str:
    """Generate a text description of an image using Gemini vision.

    Returns a concise description focused on subjects and context.
    Returns empty string on failure.
    """
    try:
        response = _get_client().models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                (
                    "Describe this image in 1-2 sentences. "
                    "Focus on SUBJECTS, ACTIONS, and CONTEXT — not colors, lighting, or image quality. "
                    "Be specific and concise."
                ),
            ],
        )
        return response.text.strip()
    except Exception as e:
        print(f"  Image description failed: {e}")
        return ""
