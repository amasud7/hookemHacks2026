"""Scrape a single URL via Apify, download the video, embed, and push to MongoDB.

Usage:
    python -m scripts.ingest_url "https://www.instagram.com/p/B7_yGl6lWq4/"
    python -m scripts.ingest_url "https://www.tiktok.com/@user/video/123"
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from scrapers import InstagramScraper, TikTokScraper
from src.ingest import ingest_content


def download_video(url: str) -> Path | None:
    output_path = Path(tempfile.mktemp(suffix=".mp4"))
    try:
        subprocess.run(
            ["yt-dlp", "--no-warnings", "-f", "mp4", "-o", str(output_path), url],
            check=True, capture_output=True, text=True,
        )
        if output_path.exists() and output_path.stat().st_size > 0:
            return output_path
    except subprocess.CalledProcessError as e:
        print(f"  Download failed: {e.stderr[:200] if e.stderr else 'unknown'}")
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.ingest_url <url>")
        sys.exit(1)

    url = sys.argv[1].split("?")[0]  # strip query params
    print(f"Processing: {url}\n")

    # Scrape metadata
    if "instagram.com" in url:
        scraper = InstagramScraper()
        results = scraper.scrape_urls([url])
    elif "tiktok.com" in url:
        scraper = TikTokScraper()
        results = scraper.scrape_urls([url])
    else:
        print(f"Unsupported platform: {url}")
        sys.exit(1)

    if not results:
        print("No results from scraper.")
        sys.exit(1)

    r = results[0]
    content_id = f"{r.platform}_{url.rstrip('/').split('/')[-1]}"

    print(f"Content ID: {content_id}")
    print(f"Author: @{r.author}")
    print(f"Caption: {r.text[:100]}...")
    print(f"Sound: {r.sound_name}")
    print()

    # Download video
    print("Downloading video...")
    video_path = download_video(url)
    if video_path:
        print(f"  Downloaded: {video_path}")
    else:
        print("  No video — will embed text only")

    # Ingest
    print("\nIngesting...")
    try:
        ingest_content(
            content_id=content_id,
            platform=r.platform,
            url=r.url or url,
            video_path=video_path,
            caption=r.text,
            creator=r.author,
            hashtags=r.hashtags,
            content_type=r.content_type,
            likes=r.likes,
            views=r.views,
            comments=r.comments,
            transcript=r.transcript,
            sound_name=r.sound_name,
        )
        print("\nDone! Embedded and pushed to MongoDB.")
    except Exception as e:
        print(f"\nERROR: {e}")
    finally:
        if video_path and video_path.exists():
            video_path.unlink()


if __name__ == "__main__":
    main()
