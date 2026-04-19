from datetime import datetime
from pydantic import BaseModel, Field


class ContentDocument(BaseModel):
    """A piece of short-form content with per-modality embeddings."""

    content_id: str
    platform: str  # tiktok, instagram, youtube
    url: str
    creator: str = ""
    caption: str = ""
    thumb: str = ""  # local thumbnail path (served by our server)
    video_url: str = ""  # local video path (served by our server)
    hashtags: list[str] = Field(default_factory=list)
    duration_seconds: float | None = None
    content_type: str = "video"  # video, slideshow, image
    has_audio: bool = True
    likes: int = 0
    views: int = 0
    comments: int = 0
    transcript: str = ""
    sound_name: str = ""
    created_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    # Per-modality embeddings (768-dim, L2-normalized)
    text_embedding: list[float] | None = None
    visual_embedding: list[float] | None = None
    audio_embedding: list[float] | None = None

    def to_mongo(self) -> dict:
        """Convert to a MongoDB document, excluding None embedding fields."""
        doc = self.model_dump()
        # Remove None embeddings so MongoDB vector search skips these docs for that modality
        for key in ("text_embedding", "visual_embedding", "audio_embedding"):
            if doc[key] is None:
                del doc[key]
        return doc


class SearchResult(BaseModel):
    """A search result returned from vector search."""

    content_id: str
    platform: str
    url: str
    creator: str = ""
    caption: str = ""
    thumb: str = ""
    video_url: str = ""
    likes: int = 0
    views: int = 0
    comments: int = 0
    score: float = 0.0
