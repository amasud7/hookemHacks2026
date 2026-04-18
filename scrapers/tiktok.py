from __future__ import annotations

from .base import BaseScraper, ScraperResult


class TikTokScraper(BaseScraper):
    """Scrapes TikTok videos via clockworks/tiktok-scraper."""

    ACTOR_ID = "clockworks/tiktok-scraper"

    def search(
        self,
        query: str,
        max_results: int = 50,
        sort: str = "0",
    ) -> list[ScraperResult]:
        """Search TikTok videos by keyword.

        Args:
            query: Search term.
            max_results: Max results to return.
            sort: "0" = most relevant, "1" = most liked, "3" = latest.
        """
        run_input = {
            "searchQueries": [query],
            "searchSection": "/video",
            "resultsPerPage": max_results,
            "searchSorting": sort,
        }
        items = self._run_actor(run_input)
        return [self._normalize(item) for item in items]

    def search_hashtag(
        self,
        hashtag: str,
        max_results: int = 50,
    ) -> list[ScraperResult]:
        """Search TikTok videos by hashtag."""
        tag = hashtag.lstrip("#")
        run_input = {
            "hashtags": [tag],
            "resultsPerPage": max_results,
        }
        items = self._run_actor(run_input)
        return [self._normalize(item) for item in items]

    def scrape_profile(
        self,
        username: str,
        max_results: int = 50,
    ) -> list[ScraperResult]:
        """Scrape a specific TikTok profile's videos."""
        run_input = {
            "profiles": [username],
            "resultsPerPage": max_results,
        }
        items = self._run_actor(run_input)
        return [self._normalize(item) for item in items]

    def scrape_urls(self, urls: list[str]) -> list[ScraperResult]:
        """Scrape metadata from a list of TikTok video URLs."""
        run_input = {
            "postURLs": urls,
        }
        items = self._run_actor(run_input)
        return [self._normalize(item) for item in items]

    def _normalize(self, item: dict) -> ScraperResult:
        media_urls = []
        if item.get("webVideoUrl"):
            media_urls.append(item["webVideoUrl"])
        for url in item.get("mediaUrls", []):
            media_urls.append(url)

        hashtags = []
        for tag in item.get("hashtags", []):
            if isinstance(tag, dict):
                hashtags.append(tag.get("name", ""))
            else:
                hashtags.append(str(tag))

        author = ""
        author_meta = item.get("authorMeta", {})
        if author_meta:
            author = author_meta.get("name", "") or author_meta.get("nickName", "")

        music_meta = item.get("musicMeta", {}) or {}

        return ScraperResult(
            platform="tiktok",
            content_type="video",
            text=item.get("text", "") or "",
            url=item.get("webVideoUrl", ""),
            media_urls=media_urls,
            author=author,
            sound_name=music_meta.get("musicName", "") or "",
            sound_author=music_meta.get("musicAuthor", "") or "",
            likes=item.get("diggCount", 0) or 0,
            comments=item.get("commentCount", 0) or 0,
            shares=item.get("shareCount", 0) or 0,
            views=item.get("playCount", 0) or 0,
            created_at=item.get("createTimeISO", ""),
            hashtags=hashtags,
            raw=item,
        )
