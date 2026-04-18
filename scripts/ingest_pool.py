"""Ingest content_pool.json + local media files into MongoDB with multimodal embeddings.

Maps local video/image files in data/raw/ to their content_pool.json entries,
then feeds each through the embedding pipeline (visual + audio + text) and
stores the result in MongoDB Atlas.

Usage:
    python -m scripts.ingest_pool
"""

import json
from pathlib import Path

from src.ingest import ingest_content

POOL_FILE = Path("content_pool.json")
DATA_DIR = Path("data/raw")

# Manual mapping: filename prefix → content_pool shortCode/id or manual label
FILE_TO_CONTENT = {
    # Instagram reels (mapped to content_pool.json by shortCode)
    "a8d6552592f1472185722a1cdcbba67d": "DUn6HCeE4by",      # 6 AI 5 parachutes
    "68460fd54e374b6384d25174441ca332": "DWyoxiCDGKg",       # cats dancing dryer
    "658d71286bb24588b0f4eb55f6510391": "DFIaEarNVA9",       # sopranos ooohh (IG)
    "89cf974726884dc1982694ecaeb573a1": "DU3rGLLDoVX",       # wilson lo siento
    "5d72eeab08b84df4b89e31494f205722": "DW7u1kPDc5Z",       # claude whip
    "0f72c215a1704ae3a9c988f6c142c3d9": "DXOCjsnDMMd",       # cat doing scuba
    # Videos not in content_pool (manual metadata)
    "641ab96e7a424edf82e63756f6c27929": "_speed_trying_not_to_laugh",
    "1f4556cd24de48409484afc4b97b837c": "_ting_ting_tung",
    # TikTok videos
    "v12025gd0000d62c4g7og65nlsh8jqa0": "_tiktok_unmapped_1",
    "v12044gd0000csjes4fog65mbccuiv60": "_tiktok_unmapped_2",
}

# Manual metadata for videos not in content_pool.json
MANUAL_METADATA = {
    "_speed_trying_not_to_laugh": {
        "platform": "instagram",
        "url": "",
        "caption": "IShowSpeed trying not to laugh challenge. Speed can't hold it in.",
        "creator": "ishowspeed",
        "hashtags": ["ishowspeed", "speed", "trynottolaugh", "funny"],
        "content_type": "video",
    },
    "_ting_ting_tung": {
        "platform": "instagram",
        "url": "",
        "caption": "Ting ting tung ting ting sound effect meme",
        "creator": "",
        "hashtags": ["tingtingtung", "meme", "soundeffect"],
        "content_type": "video",
    },
    "_tiktok_unmapped_1": {
        "platform": "tiktok",
        "url": "",
        "caption": "",
        "creator": "",
        "hashtags": [],
        "content_type": "video",
    },
    "_tiktok_unmapped_2": {
        "platform": "tiktok",
        "url": "",
        "caption": "",
        "creator": "",
        "hashtags": [],
        "content_type": "video",
    },
}


def load_pool_index() -> dict[str, dict]:
    """Index content_pool.json by shortCode and raw.id for fast lookup."""
    if not POOL_FILE.exists():
        return {}

    with open(POOL_FILE) as f:
        pool = json.load(f)

    index = {}
    for item in pool:
        raw = item.get("raw", {})
        shortcode = raw.get("shortCode", "")
        raw_id = str(raw.get("id", ""))
        if shortcode:
            index[shortcode] = item
        if raw_id:
            index[raw_id] = item
    return index


def main():
    pool_index = load_pool_index()

    # Collect all media files
    video_exts = {".mp4", ".mov", ".webm"}
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    all_exts = video_exts | image_exts

    media_files = sorted(f for f in DATA_DIR.iterdir() if f.suffix.lower() in all_exts)
    print(f"Found {len(media_files)} media files in {DATA_DIR}/\n")

    success = 0
    failed = 0

    for i, media_path in enumerate(media_files, 1):
        file_stem = media_path.stem
        content_type = "video" if media_path.suffix.lower() in video_exts else "image"

        # Look up mapping
        content_key = FILE_TO_CONTENT.get(file_stem, "")

        print(f"\n[{i}/{len(media_files)}] {media_path.name}")

        if content_key and not content_key.startswith("_"):
            # Mapped to a content_pool.json entry
            pool_item = pool_index.get(content_key)
            if not pool_item:
                print(f"  WARNING: Key '{content_key}' not found in content_pool.json, skipping")
                failed += 1
                continue

            content_id = f"{pool_item['platform']}_{content_key}"
            caption = pool_item.get("text", "")
            transcript = pool_item.get("transcript", "")
            if transcript:
                caption += f"\n\nTranscript: {transcript}"
            sound_name = pool_item.get("sound_name", "")
            sound_author = pool_item.get("sound_author", "")
            if sound_name:
                caption += f"\n\nSound: {sound_name}"
                if sound_author:
                    caption += f" by {sound_author}"

            try:
                ingest_content(
                    content_id=content_id,
                    platform=pool_item["platform"],
                    url=pool_item.get("url", ""),
                    video_path=media_path,
                    caption=caption,
                    creator=pool_item.get("author", ""),
                    hashtags=pool_item.get("hashtags", []),
                    content_type=content_type,
                )
                success += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                failed += 1

        elif content_key and content_key.startswith("_"):
            # Manual metadata (not in pool)
            meta = MANUAL_METADATA.get(content_key, {})
            content_id = f"{meta.get('platform', 'unknown')}_{file_stem[:12]}"

            try:
                ingest_content(
                    content_id=content_id,
                    platform=meta.get("platform", "unknown"),
                    url=meta.get("url", ""),
                    video_path=media_path,
                    caption=meta.get("caption", ""),
                    creator=meta.get("creator", ""),
                    hashtags=meta.get("hashtags", []),
                    content_type=content_type,
                )
                success += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                failed += 1

        else:
            # Unmapped file (images, etc.) — ingest with filename as caption
            content_id = f"unknown_{file_stem[:16]}"
            caption = file_stem.replace("_", " ").replace("-", " ")

            try:
                ingest_content(
                    content_id=content_id,
                    platform="unknown",
                    url="",
                    video_path=media_path,
                    caption=caption,
                    content_type=content_type,
                )
                success += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                failed += 1

    print(f"\n{'='*60}")
    print(f"Done! {success} ingested, {failed} failed out of {len(media_files)} total.")


if __name__ == "__main__":
    main()
