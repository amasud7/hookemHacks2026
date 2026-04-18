from pathlib import Path
from datetime import datetime

from src.db import get_collection
from src.embeddings import embed_text, embed_video, embed_audio
from src.media import extract_audio
from src.models import ContentDocument


def ingest_content(
    content_id: str,
    platform: str,
    url: str,
    video_path: str | Path | None = None,
    caption: str = "",
    creator: str = "",
    hashtags: list[str] | None = None,
    duration_seconds: float | None = None,
    content_type: str = "video",
    created_at: datetime | None = None,
) -> ContentDocument:
    """Ingest a single piece of content: embed all available modalities and store in MongoDB.

    Args:
        content_id: Unique identifier (e.g. platform_postid)
        platform: Source platform (tiktok, instagram, youtube)
        url: Original content URL
        video_path: Path to downloaded video/image file. None if only text metadata available.
        caption: Post caption/description
        creator: Creator username
        hashtags: List of hashtags
        duration_seconds: Content duration
        content_type: "video", "slideshow", or "image"
        created_at: Original post timestamp
    """
    text_emb = None
    visual_emb = None
    audio_emb = None
    has_audio = False

    # 1. Embed visual content (video or image)
    if video_path is not None:
        video_path = Path(video_path)
        video_bytes = video_path.read_bytes()

        mime_map = {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".webm": "video/webm",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        mime_type = mime_map.get(video_path.suffix.lower(), "video/mp4")

        print(f"  Embedding visual for {content_id}...")
        visual_emb = embed_video(video_bytes, mime_type=mime_type)

        # 2. Extract audio, transcribe, and embed (only for video content)
        if content_type == "video":
            print(f"  Extracting audio for {content_id}...")
            audio_path = extract_audio(video_path)
            if audio_path is not None:
                has_audio = True
                audio_bytes = audio_path.read_bytes()

                print(f"  Embedding audio for {content_id}...")
                audio_emb = embed_audio(audio_bytes)
                audio_path.unlink()  # clean up temp file

    # 3. Embed text (caption + hashtags)
    text_blob = caption
    if hashtags:
        text_blob += " " + " ".join(f"#{tag}" for tag in hashtags)
    if text_blob.strip():
        print(f"  Embedding text for {content_id}...")
        text_emb = embed_text(text_blob)

    doc = ContentDocument(
        content_id=content_id,
        platform=platform,
        url=url,
        creator=creator,
        caption=caption,
        hashtags=hashtags or [],
        duration_seconds=duration_seconds,
        content_type=content_type,
        has_audio=has_audio,
        created_at=created_at,
        text_embedding=text_emb,
        visual_embedding=visual_emb,
        audio_embedding=audio_emb,
    )

    collection = get_collection()
    # Upsert by content_id so re-ingestion is safe
    collection.replace_one(
        {"content_id": content_id},
        doc.to_mongo(),
        upsert=True,
    )
    print(f"  Stored {content_id} in MongoDB.")
    return doc


def ingest_batch(items: list[dict]) -> list[ContentDocument]:
    """Ingest multiple content items. Each dict is passed as kwargs to ingest_content.

    Expected dict keys match ingest_content params:
        content_id, platform, url, video_path, caption, creator, hashtags, etc.
    """
    results = []
    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] Ingesting {item.get('content_id', 'unknown')}...")
        doc = ingest_content(**item)
        results.append(doc)
    return results
