from pathlib import Path
from datetime import datetime

from src.db import get_collection
from src.describe import describe_video, describe_image
from src.embeddings import embed_text, embed_video, embed_audio
from src.media import extract_audio
from src.models import ContentDocument
from src.transcribe import transcribe_audio as whisper_transcribe


def ingest_content(
    content_id: str,
    platform: str,
    url: str,
    video_path: str | Path | None = None,
    video_bytes: bytes | None = None,
    video_mime: str = "video/mp4",
    audio_bytes: bytes | None = None,
    audio_mime: str = "audio/mpeg",
    caption: str = "",
    creator: str = "",
    thumb: str = "",
    video_url: str = "",
    hashtags: list[str] | None = None,
    duration_seconds: float | None = None,
    content_type: str = "video",
    likes: int = 0,
    views: int = 0,
    comments: int = 0,
    transcript: str = "",
    sound_name: str = "",
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
    description_emb = None
    description = ""
    has_audio = False

    # 1. Embed visual content — from bytes or file path
    if video_bytes is not None:
        print(f"  Embedding visual for {content_id}...")
        visual_emb = embed_video(video_bytes, mime_type=video_mime)
    elif video_path is not None:
        video_path = Path(video_path)
        raw_bytes = video_path.read_bytes()
        mime_map = {
            ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm",
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        }
        mime_type = mime_map.get(video_path.suffix.lower(), "video/mp4")
        print(f"  Embedding visual for {content_id}...")
        visual_emb = embed_video(raw_bytes, mime_type=mime_type)

        # Extract audio from local file if no audio_bytes provided
        if content_type == "video" and audio_bytes is None:
            print(f"  Extracting audio for {content_id}...")
            extracted = extract_audio(video_path)
            if extracted is not None:
                audio_bytes = extracted.read_bytes()
                audio_mime = "audio/mpeg"
                extracted.unlink()

    # 2. Embed audio + transcribe with Whisper if no transcript provided
    if audio_bytes is not None:
        has_audio = True
        print(f"  Embedding audio for {content_id}...")
        audio_emb = embed_audio(audio_bytes, mime_type=audio_mime)

        if not transcript:
            print(f"  Transcribing audio with Whisper for {content_id}...")
            suffix = ".mp3" if "mpeg" in audio_mime else ".mp4" if "mp4" in audio_mime else ".webm"
            transcript = whisper_transcribe(audio_bytes, suffix=suffix)
            if transcript:
                print(f"  Transcript: {transcript[:100]}{'...' if len(transcript) > 100 else ''}")

    # 3. Generate and embed video description (action-focused, lighting-invariant)
    vid_bytes = video_bytes
    if vid_bytes is None and video_path is not None:
        vid_bytes = Path(video_path).read_bytes() if Path(video_path).exists() else None
    if vid_bytes is not None:
        if content_type == "video":
            print(f"  Describing video for {content_id}...")
            description = describe_video(vid_bytes)
        else:
            print(f"  Describing image for {content_id}...")
            description = describe_image(vid_bytes)
        if description:
            print(f"  Description: {description[:100]}{'...' if len(description) > 100 else ''}")
            description_emb = embed_text(description)

    # 4. Embed text (caption + hashtags + transcript)
    text_blob = caption
    if hashtags:
        text_blob += " " + " ".join(f"#{tag}" for tag in hashtags)
    if transcript:
        text_blob += " " + transcript
    if text_blob.strip():
        print(f"  Embedding text for {content_id}...")
        text_emb = embed_text(text_blob)

    doc = ContentDocument(
        content_id=content_id,
        platform=platform,
        url=url,
        creator=creator,
        caption=caption,
        thumb=thumb,
        video_url=video_url,
        hashtags=hashtags or [],
        duration_seconds=duration_seconds,
        content_type=content_type,
        has_audio=has_audio,
        likes=likes,
        views=views,
        comments=comments,
        transcript=transcript,
        sound_name=sound_name,
        description=description,
        created_at=created_at,
        text_embedding=text_emb,
        visual_embedding=visual_emb,
        audio_embedding=audio_emb,
        description_embedding=description_emb,
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
