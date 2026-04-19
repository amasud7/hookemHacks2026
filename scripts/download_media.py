"""Download thumbnails and videos from content_pool.json CDN URLs to local storage.

Saves files to frontend/media/ so they're served by FastAPI.
Updates MongoDB documents with local paths.

Usage:
    python -m scripts.download_media
"""

import json
from pathlib import Path
from urllib.request import urlopen, Request

from src.db import get_collection

POOL_FILE = Path("content_pool.json")
MEDIA_DIR = Path("frontend/media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def download_url(url: str, dest: Path, timeout: int = 30) -> bool:
    """Download a URL to a local file. Returns True on success."""
    if dest.exists() and dest.stat().st_size > 0:
        print(f"    Already exists: {dest.name}")
        return True
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        dest.write_bytes(data)
        print(f"    Downloaded: {dest.name} ({len(data) / 1024:.0f} KB)")
        return True
    except Exception as e:
        print(f"    Failed: {e}")
        return False


def extract_urls(item: dict) -> tuple[str, str]:
    """Extract thumbnail (.jpg) and video (.mp4) URLs from media_urls."""
    thumb_url = ""
    video_url = ""
    for u in item.get("media_urls", []):
        path_part = u.split("?")[0]
        if path_part.endswith((".jpg", ".jpeg", ".png", ".webp")):
            thumb_url = u
        elif path_part.endswith((".mp4", ".mov", ".webm")):
            if not video_url:  # take first video URL
                video_url = u
    return thumb_url, video_url


def get_content_id(item: dict) -> str:
    """Build the content_id matching what ingest_pool.py uses."""
    raw = item.get("raw", {})
    shortcode = raw.get("shortCode", "")
    return f"{item['platform']}_{shortcode}" if shortcode else ""


def main():
    if not POOL_FILE.exists():
        print(f"File not found: {POOL_FILE}")
        return

    with open(POOL_FILE) as f:
        items = json.load(f)

    collection = get_collection()
    print(f"Processing {len(items)} items from {POOL_FILE}\n")

    for i, item in enumerate(items, 1):
        content_id = get_content_id(item)
        if not content_id:
            print(f"[{i}] Skipping (no shortCode)")
            continue

        thumb_url, video_url = extract_urls(item)
        print(f"[{i}/{len(items)}] {content_id}")

        local_thumb = ""
        local_video = ""

        # Download thumbnail
        if thumb_url:
            thumb_path = MEDIA_DIR / f"{content_id}_thumb.jpg"
            if download_url(thumb_url, thumb_path):
                local_thumb = f"/media/{thumb_path.name}"

        # Download video
        if video_url:
            video_path = MEDIA_DIR / f"{content_id}_video.mp4"
            if download_url(video_url, video_path):
                local_video = f"/media/{video_path.name}"

        # Update MongoDB with local paths
        update = {}
        if local_thumb:
            update["thumb"] = local_thumb
        if local_video:
            update["video_url"] = local_video

        if update:
            result = collection.update_one(
                {"content_id": content_id},
                {"$set": update},
            )
            if result.modified_count:
                print(f"    Updated MongoDB: {list(update.keys())}")
            elif result.matched_count:
                print(f"    Already up to date")
            else:
                print(f"    Not found in MongoDB (content_id={content_id})")

        print()

    print("Done! Media files saved to frontend/media/")


if __name__ == "__main__":
    main()
