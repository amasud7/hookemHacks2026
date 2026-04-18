from __future__ import annotations

from .base import BaseScraper, ScraperResult


class InstagramScraper(BaseScraper):
    """Scrapes Instagram posts and reels.

    Uses apify/instagram-reel-scraper for reels (returns music info, transcript, audio URL).
    Uses apify/instagram-scraper for posts.
    """

    ACTOR_ID = "apify/instagram-scraper"
    REEL_ACTOR_ID = "apify/instagram-reel-scraper"

    def search(
        self,
        query: str,
        max_results: int = 50,
        content_type: str = "posts",
    ) -> list[ScraperResult]:
        """Search Instagram by hashtag query.

        Args:
            query: Search term (hashtag-style, e.g. "funny cats").
            max_results: Max results to return.
            content_type: "posts" | "reels"
        """
        if content_type == "reels":
            # Use the reel scraper's search via hashtag profile
            run_input = {
                "username": [f"https://www.instagram.com/explore/tags/{query}/"],
                "resultsLimit": max_results,
                "includeTranscript": True,
            }
            items = self._run_reel_actor(run_input)
            return [self._normalize_reel(item) for item in items]
        else:
            run_input = {
                "search": query,
                "searchType": "hashtag",
                "resultsType": content_type,
                "resultsLimit": max_results,
            }
            items = self._run_actor(run_input)
            return [self._normalize_post(item) for item in items]

    def scrape_urls(
        self,
        urls: list[str],
        include_transcript: bool = True,
    ) -> list[ScraperResult]:
        """Scrape metadata from a list of Instagram post/reel URLs.

        Uses the reel scraper for reel URLs (better audio/music metadata).
        Falls back to generic scraper for post URLs.
        """
        reel_urls = [u for u in urls if "/reel/" in u]
        post_urls = [u for u in urls if "/reel/" not in u]

        results = []

        if reel_urls:
            run_input = {
                "username": reel_urls,
                "includeTranscript": include_transcript,
            }
            items = self._run_reel_actor(run_input)
            results.extend(self._normalize_reel(item) for item in items)

        if post_urls:
            run_input = {
                "directUrls": post_urls,
                "resultsType": "posts",
                "resultsLimit": 1,
            }
            items = self._run_actor(run_input)
            results.extend(self._normalize_post(item) for item in items)

        return results

    def scrape_profile(
        self,
        username: str,
        max_results: int = 50,
        content_type: str = "reels",
    ) -> list[ScraperResult]:
        """Scrape a specific Instagram profile's content."""
        if content_type == "reels":
            run_input = {
                "username": [username],
                "resultsLimit": max_results,
                "includeTranscript": True,
            }
            items = self._run_reel_actor(run_input)
            return [self._normalize_reel(item) for item in items]
        else:
            run_input = {
                "directUrls": [f"https://www.instagram.com/{username}/"],
                "resultsType": content_type,
                "resultsLimit": max_results,
            }
            items = self._run_actor(run_input)
            return [self._normalize_post(item) for item in items]

    def _run_reel_actor(self, run_input: dict) -> list[dict]:
        """Run the reel-specific actor."""
        run = self.client.actor(self.REEL_ACTOR_ID).call(run_input=run_input)
        return list(self.client.dataset(run["defaultDatasetId"]).iterate_items())

    def _normalize_reel(self, item: dict) -> ScraperResult:
        """Normalize output from apify/instagram-reel-scraper."""
        media_urls = []
        if item.get("videoUrl"):
            media_urls.append(item["videoUrl"])
        if item.get("audioUrl"):
            media_urls.append(item["audioUrl"])
        if item.get("displayUrl"):
            media_urls.append(item["displayUrl"])

        music_info = item.get("musicInfo", {}) or {}

        return ScraperResult(
            platform="instagram",
            content_type="video",
            text=item.get("caption", "") or "",
            url=item.get("url", ""),
            media_urls=media_urls,
            author=item.get("ownerUsername", "") or item.get("ownerFullName", ""),
            sound_name=music_info.get("song_name", "") or "",
            sound_author=music_info.get("artist_name", "") or "",
            audio_url=item.get("audioUrl", "") or "",
            transcript=item.get("transcript", "") or "",
            likes=item.get("likesCount", 0) or 0,
            comments=item.get("commentsCount", 0) or 0,
            shares=item.get("sharesCount", 0) or 0,
            views=item.get("videoViewCount", 0) or item.get("videoPlayCount", 0) or 0,
            created_at=item.get("timestamp", ""),
            hashtags=item.get("hashtags", []) or [],
            raw=item,
        )

    def _normalize_post(self, item: dict) -> ScraperResult:
        """Normalize output from apify/instagram-scraper (posts)."""
        item_type = item.get("type", "")
        if item_type in ("Video", "video"):
            ct = "video"
        elif item_type in ("Sidecar", "sidecar"):
            ct = "slideshow"
        else:
            ct = "image"

        media_urls = []
        if item.get("videoUrl"):
            media_urls.append(item["videoUrl"])
        if item.get("displayUrl"):
            media_urls.append(item["displayUrl"])
        for img in item.get("images", []):
            if isinstance(img, str):
                media_urls.append(img)
            elif isinstance(img, dict) and img.get("url"):
                media_urls.append(img["url"])

        music_info = item.get("musicInfo", {}) or {}

        return ScraperResult(
            platform="instagram",
            content_type=ct,
            text=item.get("caption", "") or "",
            url=item.get("url", ""),
            media_urls=media_urls,
            author=item.get("ownerUsername", "") or item.get("ownerFullName", ""),
            sound_name=music_info.get("song_name", "") or music_info.get("music_title", "") or "",
            sound_author=music_info.get("artist_name", "") or music_info.get("music_author", "") or "",
            audio_url="",
            transcript="",
            likes=item.get("likesCount", 0) or 0,
            comments=item.get("commentsCount", 0) or 0,
            shares=0,
            views=item.get("videoViewCount", 0) or 0,
            created_at=item.get("timestamp", ""),
            hashtags=item.get("hashtags", []) or [],
            raw=item,
        )
