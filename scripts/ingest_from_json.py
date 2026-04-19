"""Ingest content from Apify JSON + uploads/ folder in one command.

Reads the JSON, downloads videos/thumbnails from CDN URLs, also ingests
any photos/videos from uploads/, embeds all modalities, and stores in MongoDB.

Usage:
    python -m scripts.ingest_from_json                          # defaults to content_pool.json + uploads/
    python -m scripts.ingest_from_json --file my_scrape.json    # custom JSON file
    python -m scripts.ingest_from_json --skip-existing          # skip items already in MongoDB
    python -m scripts.ingest_from_json --json-only              # skip uploads/ folder
    python -m scripts.ingest_from_json --uploads-only           # skip JSON, only process uploads/
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request

from src.ingest import ingest_content
from src.db import get_collection

MEDIA_DIR = Path("frontend/media")
UPLOADS_DIR = Path("uploads")
VIDEO_EXTS = {".mp4", ".mov", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic"}
UPLOAD_EXTS = VIDEO_EXTS | IMAGE_EXTS


def download_url(url: str, dest: Path, timeout: int = 60) -> bool:
    """Download a URL to a local file. Skips if already exists with content."""
    if dest.exists() and dest.stat().st_size > 0:
        return True
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=timeout) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def download_bytes(url: str, timeout: int = 60) -> bytes | None:
    """Download a URL and return raw bytes."""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"    Download failed: {e}")
        return None


def parse_media_urls(media_urls: list[str]) -> dict:
    """Categorize media URLs into video, audio, and thumbnail."""
    result = {"video_cdn": "", "thumb_cdn": ""}
    for u in media_urls:
        path_part = u.split("?")[0]
        if path_part.endswith((".jpg", ".jpeg", ".png", ".webp")) and not result["thumb_cdn"]:
            result["thumb_cdn"] = u
        elif path_part.endswith((".mp4", ".mov", ".webm")) and not result["video_cdn"]:
            result["video_cdn"] = u
    return result


def build_content_id(item: dict) -> str:
    """Build a unique content_id from the item."""
    raw = item.get("raw", {})
    platform = item.get("platform", "unknown")
    # Try shortCode first, then raw id, then hash of URL
    identifier = raw.get("shortCode") or str(raw.get("id", ""))
    if not identifier:
        # Fallback: use last segment of URL
        identifier = item.get("url", "").rstrip("/").split("/")[-1]
    if not identifier:
        identifier = str(hash(json.dumps(item, sort_keys=True, default=str)))[:12]
    return f"{platform}_{identifier}"


def ingest_uploads(existing_ids: set, skip_existing: bool) -> tuple[int, int, int]:
    """Ingest photos and videos from uploads/ folder. Returns (success, skipped, failed)."""
    if not UPLOADS_DIR.exists():
        return 0, 0, 0

    files = sorted(f for f in UPLOADS_DIR.iterdir() if f.suffix.lower() in UPLOAD_EXTS)
    if not files:
        return 0, 0, 0

    print(f"\n{'=' * 60}")
    print(f"UPLOADS: Found {len(files)} file(s) in uploads/\n")

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
            local_video = f"/media/{media_dest.name}"
            local_thumb = ""
        else:
            media_dest = MEDIA_DIR / f"{content_id}_thumb{file_path.suffix.lower()}"
            local_thumb = f"/media/{media_dest.name}"
            local_video = ""

        shutil.copy2(file_path, media_dest)

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

    return success, skipped, failed


def main():
    # Parse args
    pool_path = "content_pool.json"
    skip_existing = "--skip-existing" in sys.argv
    json_only = "--json-only" in sys.argv
    uploads_only = "--uploads-only" in sys.argv
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        pool_path = sys.argv[idx + 1]

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    # Get existing content_ids if skipping
    existing_ids = set()
    if skip_existing:
        collection = get_collection()
        existing_ids = {doc["content_id"] for doc in collection.find({}, {"content_id": 1, "_id": 0})}
        print(f"Found {len(existing_ids)} existing items in MongoDB\n")

    total_success = 0
    total_skipped = 0
    total_failed = 0

    # --- Part 1: Apify JSON ---
    if not uploads_only:
        pool_path = Path(pool_path)
        if not pool_path.exists():
            print(f"JSON file not found: {pool_path}, skipping JSON ingestion")
        else:
            with open(pool_path) as f:
                items = json.load(f)

            print(f"JSON: Processing {len(items)} items from {pool_path}\n")

            success = 0
            skipped = 0
            failed = 0

            for i, item in enumerate(items, 1):
                content_id = build_content_id(item)
                platform = item.get("platform", "unknown")
                caption = item.get("text", "")

                print(f"[{i}/{len(items)}] {content_id} ({platform})")

                if skip_existing and content_id in existing_ids:
                    print(f"  Already exists, skipping")
                    skipped += 1
                    continue

                # Parse media URLs
                media = parse_media_urls(item.get("media_urls", []))

                # Download thumbnail to local storage
                local_thumb = ""
                if media["thumb_cdn"]:
                    thumb_path = MEDIA_DIR / f"{content_id}_thumb.jpg"
                    print(f"  Downloading thumbnail...")
                    if download_url(media["thumb_cdn"], thumb_path):
                        local_thumb = f"/media/{thumb_path.name}"

                # Download video to local storage AND get bytes for embedding
                local_video = ""
                video_bytes = None
                if media["video_cdn"]:
                    video_path = MEDIA_DIR / f"{content_id}_video.mp4"
                    print(f"  Downloading video...")
                    if download_url(media["video_cdn"], video_path):
                        local_video = f"/media/{video_path.name}"
                        video_bytes = video_path.read_bytes()
                        print(f"  Video: {len(video_bytes) / 1024 / 1024:.1f} MB")

                # Download audio if separate URL provided
                audio_bytes = None
                audio_url = item.get("audio_url", "")
                if audio_url:
                    print(f"  Downloading audio...")
                    audio_bytes = download_bytes(audio_url)
                    if audio_bytes:
                        print(f"  Audio: {len(audio_bytes) / 1024:.0f} KB")

                # Parse created_at
                created_at = None
                if item.get("created_at"):
                    try:
                        created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass

                # Ingest with all data
                try:
                    ingest_content(
                        content_id=content_id,
                        platform=platform,
                        url=item.get("url", ""),
                        video_bytes=video_bytes,
                        video_mime="video/mp4",
                        audio_bytes=audio_bytes,
                        audio_mime="audio/mp4",
                        caption=caption,
                        creator=item.get("author", ""),
                        thumb=local_thumb,
                        video_url=local_video,
                        hashtags=item.get("hashtags", []),
                        content_type=item.get("content_type", "video"),
                        likes=item.get("likes", 0),
                        views=item.get("views", 0),
                        comments=item.get("comments", 0),
                        transcript=item.get("transcript", ""),
                        sound_name=item.get("sound_name", ""),
                        created_at=created_at,
                    )
                    success += 1
                except Exception as e:
                    print(f"  ERROR: {e}")
                    failed += 1

                print()

            total_success += success
            total_skipped += skipped
            total_failed += failed
            print(f"\nJSON: {success} ingested, {skipped} skipped, {failed} failed")

    # --- Part 2: Uploads folder ---
    if not json_only:
        s, sk, f = ingest_uploads(existing_ids, skip_existing)
        total_success += s
        total_skipped += sk
        total_failed += f
        if s or sk or f:
            print(f"Uploads: {s} ingested, {sk} skipped, {f} failed")

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total_success} ingested, {total_skipped} skipped, {total_failed} failed")


if __name__ == "__main__":
    main()
