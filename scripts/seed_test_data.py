"""Seed test data by ingesting local video files from data/raw/.

Place a few short video files (mp4) in data/raw/ and run:
    python -m scripts.seed_test_data

Each video file becomes a content document with text (filename-derived),
visual, and audio embeddings.
"""

from pathlib import Path
from src.ingest import ingest_content

DATA_DIR = Path("data/raw")


def main():
    if not DATA_DIR.exists():
        print(f"No data directory found at {DATA_DIR}. Create it and add some .mp4 files.")
        return

    video_exts = {".mp4", ".mov", ".webm"}
    image_exts = {".jpg", ".jpeg", ".png"}
    all_exts = video_exts | image_exts

    media_files = [f for f in DATA_DIR.iterdir() if f.suffix.lower() in all_exts]
    if not media_files:
        print(f"No media files found in {DATA_DIR}/. Add .mp4, .mov, .jpg, or .png files.")
        return

    print(f"Found {len(media_files)} file(s) to ingest.\n")

    for media_path in media_files:
        content_id = f"test_{media_path.stem}"
        caption = media_path.stem.replace("_", " ").replace("-", " ")
        content_type = "video" if media_path.suffix.lower() in video_exts else "image"

        print(f"--- Ingesting: {media_path.name} ({content_type}) ---")
        ingest_content(
            content_id=content_id,
            platform="test",
            url=f"file://{media_path.resolve()}",
            video_path=media_path,
            caption=caption,
            content_type=content_type,
        )
        print()

    print("Seeding complete. Run a search to test:")
    print('  python -c "from src.search import search; print(search(\'your query here\'))"')


if __name__ == "__main__":
    main()
