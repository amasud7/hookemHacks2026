import base64
import subprocess
import tempfile
from pathlib import Path

from groq import Groq

from src.config import GROQ_API_KEY

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
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
    """Generate a text description of video content using Groq vision.

    Extracts key frames, sends them to Groq's vision model, and returns
    a concise description focused on actions and events (not colors/lighting).
    Returns empty string on failure.
    """
    try:
        frames = extract_frames(video_bytes, num_frames=4, suffix=suffix)
        if not frames:
            return ""

        image_parts = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64.b64encode(f).decode()}"
                },
            }
            for f in frames
        ]

        response = _get_client().chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "These are frames from a short-form video (TikTok/Instagram Reel). "
                                "Describe what is HAPPENING in this video in 1-2 sentences. "
                                "Focus on ACTIONS, MOTION, EVENTS, and SUBJECTS — not colors, lighting, or image quality. "
                                "Be specific and concise."
                            ),
                        },
                        *image_parts,
                    ],
                }
            ],
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  Video description failed: {e}")
        return ""


def describe_image(image_bytes: bytes) -> str:
    """Generate a text description of an image using Groq vision.

    Returns a concise description focused on subjects and context.
    Returns empty string on failure.
    """
    try:
        response = _get_client().chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Describe this image in 1-2 sentences. "
                                "Focus on SUBJECTS, ACTIONS, and CONTEXT — not colors, lighting, or image quality. "
                                "Be specific and concise."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  Video description failed: {e}")
        return ""
