import base64
import subprocess
import tempfile
from pathlib import Path

import anthropic

from src.config import ANTHROPIC_API_KEY

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def extract_frames(video_bytes: bytes, num_frames: int = 4, suffix: str = ".mp4") -> list[bytes]:
    """Extract evenly-spaced JPEG frames from video using ffmpeg."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(video_bytes)
        video_path = f.name

    out_dir = tempfile.mkdtemp()
    try:
        # Use ffmpeg to extract frames at even intervals
        subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-vf", f"select=not(mod(n\\,max(1\\,floor(n_frames/{num_frames})))),scale=512:-1",
                "-vsync", "vfr",
                "-frames:v", str(num_frames),
                "-q:v", "3",
                f"{out_dir}/frame_%03d.jpg",
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        # Fallback: just grab first N frames
        subprocess.run(
            [
                "ffmpeg", "-i", video_path,
                "-vf", "fps=1,scale=512:-1",
                "-frames:v", str(num_frames),
                "-q:v", "3",
                f"{out_dir}/frame_%03d.jpg",
            ],
            capture_output=True,
        )

    frames = []
    for frame_path in sorted(Path(out_dir).glob("frame_*.jpg")):
        frames.append(frame_path.read_bytes())
        frame_path.unlink()

    Path(video_path).unlink(missing_ok=True)
    Path(out_dir).rmdir()
    return frames


def describe_video(video_bytes: bytes, suffix: str = ".mp4") -> str:
    """Generate a text description of video content using Claude.

    Extracts key frames, sends them to Claude's vision, and returns
    a concise description focused on actions and events.
    Returns empty string on failure.
    """
    try:
        frames = extract_frames(video_bytes, num_frames=4, suffix=suffix)
        if not frames:
            return ""

        image_blocks = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.b64encode(f).decode(),
                },
            }
            for f in frames
        ]

        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[
                {
                    "role": "user",
                    "content": [
                        *image_blocks,
                        {
                            "type": "text",
                            "text": (
                                "These are frames from a short-form video (TikTok/Instagram Reel). "
                                "Describe what is HAPPENING in this video in 1-2 sentences. "
                                "Focus on ACTIONS, MOTION, EVENTS, and SUBJECTS — not colors, lighting, or image quality. "
                                "Be specific and concise."
                            ),
                        },
                    ],
                }
            ],
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  Video description failed: {e}")
        return ""


def describe_image(image_bytes: bytes) -> str:
    """Generate a text description of an image using Claude.

    Returns a concise description focused on subjects and context.
    Returns empty string on failure.
    """
    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64.b64encode(image_bytes).decode(),
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Describe this image in 1-2 sentences. "
                                "Focus on SUBJECTS, ACTIONS, and CONTEXT — not colors, lighting, or image quality. "
                                "Be specific and concise."
                            ),
                        },
                    ],
                }
            ],
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  Image description failed: {e}")
        return ""
