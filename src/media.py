import subprocess
import tempfile
from pathlib import Path


def extract_audio(video_path: str | Path, output_path: str | Path | None = None) -> Path | None:
    """Extract audio track from a video file to mp3 using ffmpeg.

    Returns the output path on success, None if the video has no audio track.
    If output_path is not provided, creates a temp file.
    """
    video_path = Path(video_path)
    if output_path is None:
        output_path = Path(tempfile.mktemp(suffix=".mp3"))
    else:
        output_path = Path(output_path)

    try:
        subprocess.run(
            [
                "ffmpeg", "-i", str(video_path),
                "-vn",                  # discard video
                "-acodec", "libmp3lame",
                "-q:a", "4",            # reasonable quality
                "-y",                   # overwrite output
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )
        # ffmpeg may succeed but produce an empty file if there's no audio
        if output_path.stat().st_size == 0:
            output_path.unlink()
            return None
        return output_path
    except subprocess.CalledProcessError:
        # Video has no audio track or ffmpeg error
        if output_path.exists():
            output_path.unlink()
        return None
