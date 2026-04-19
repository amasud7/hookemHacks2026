"""Ingest photos and videos from the uploads/ folder into the content pool.

Drop any images or videos into uploads/ and run this script.
Each file gets embedded, stored in MongoDB, and its thumbnail/video
is copied to frontend/media/ for display.

Usage:
    python -m scripts.ingest_uploads
    python -m scripts.ingest_uploads --skip-existing
"""

import shutil
import sys
from pathlib import Path

from src.ingest import ingest_content

UPLOADS_DIR = Path("uploads")
MEDIA_DIR = Path("frontend/media")

VIDEO_EXTS = {".mp4", ".mov", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic"}
ALL_EXTS = VIDEO_EXTS | IMAGE_EXTS


def main():
    skip_existing = "--skip-existing" in sys.argv
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    if not UPLOADS_DIR.exists():
        print(f"No uploads/ folder found. Create it and add photos/videos.")
        return

    files = sorted(f for f in UPLOADS_DIR.iterdir() if f.suffix.lower() in ALL_EXTS)
    if not files:
        print(f"No media files in uploads/. Add .jpg, .png, .mp4, or .mov files.")
        return

    # Check existing if needed
    existing_ids = set()
    if skip_existing:
        from src.db import get_collection
        existing_ids = {doc["content_id"] for doc in get_collection().find({}, {"content_id": 1, "_id": 0})}

    print(f"Found {len(files)} file(s) in uploads/\n")

    success = 0
    skipped = 0
    failed = 0

    for i, file_path in enumerate(files, 1):
        content_id = f"upload_{file_path.stem}"
        is_video = file_path.suffix.lower() in VIDEO_EXTS
        content_type = "video" if is_video else "image"

        print(f"[{i}/{len(files)}] {file_path.name} ({content_type})")

        if skip_existing and content_id in existing_ids:
            print(f"  Already exists, skipping")
            skipped += 1
            continue

        # Copy to frontend/media/ for serving
        if is_video:
            media_dest = MEDIA_DIR / f"{content_id}_video.mp4"
            thumb_dest = None
            local_video = f"/media/{media_dest.name}"
            local_thumb = ""
        else:
            media_dest = MEDIA_DIR / f"{content_id}_thumb{file_path.suffix.lower()}"
            thumb_dest = media_dest
            local_thumb = f"/media/{media_dest.name}"
            local_video = ""

        shutil.copy2(file_path, media_dest)
        print(f"  Copied to {media_dest.name}")

        # Use filename as caption
        caption = file_path.stem.replace("_", " ").replace("-", " ")

        try:
            ingest_content(
                content_id=content_id,
                platform="upload",
                url="",
                video_path=file_path,
                caption=caption,
                content_type=content_type,
                thumb=local_thumb,
                video_url=local_video,
            )
            success += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

        print()

    print(f"{'=' * 60}")
    print(f"Done! {success} ingested, {skipped} skipped, {failed} failed out of {len(files)} total.")


if __name__ == "__main__":
    main()
