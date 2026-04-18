from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ScraperResult:
    """Normalized result from any platform scraper."""

    platform: str
    content_type: str  # "video" | "image" | "slideshow"
    text: str  # caption / description
    url: str  # link to original content
    media_urls: list[str] = field(default_factory=list)
    author: str = ""
    sound_name: str = ""  # audio/music track name
    sound_author: str = ""  # original audio creator
    audio_url: str = ""  # direct audio stream URL
    transcript: str = ""  # audio transcript
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    created_at: str = ""
    hashtags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


class BaseScraper:
    """Base class for all Apify-backed scrapers."""

    ACTOR_ID: str = ""

    def __init__(self, api_token: str | None = None):
        token = api_token or os.getenv("APIFY_API_TOKEN")
        if not token:
            raise ValueError(
                "APIFY_API_TOKEN must be set in environment or passed explicitly"
            )
        self.client = ApifyClient(token)

    def _run_actor(self, run_input: dict[str, Any]) -> list[dict[str, Any]]:
        """Run the actor and return the dataset items."""
        run = self.client.actor(self.ACTOR_ID).call(run_input=run_input)
        items = list(
            self.client.dataset(run["defaultDatasetId"]).iterate_items()
        )
        return items

    def search(self, query: str, max_results: int = 50) -> list[ScraperResult]:
        raise NotImplementedError
