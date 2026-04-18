"""Quick smoke test for Instagram and TikTok scrapers."""

from scrapers import InstagramScraper, TikTokScraper

QUERY = "funny cats"
MAX_RESULTS = 5


def test_platform(name, scraper, **kwargs):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    try:
        results = scraper.search(QUERY, max_results=MAX_RESULTS, **kwargs)
        print(f"Got {len(results)} results\n")
        for r in results:
            print(f"[{r.content_type}] @{r.author}")
            print(f"  {r.text[:100]}{'...' if len(r.text) > 100 else ''}")
            print(f"  sound: {r.sound_name} — {r.sound_author}")
            print(f"  transcript: {r.transcript[:80]}..." if r.transcript else "  transcript: (none)")
            print(f"  url: {r.url}")
            print(f"  likes: {r.likes}  comments: {r.comments}  views: {r.views}")
            print(f"  media_urls: {len(r.media_urls)}")
            print()
    except Exception as e:
        print(f"ERROR: {e}\n")


if __name__ == "__main__":
    test_platform("Instagram (posts)", InstagramScraper(), content_type="posts")
    test_platform("Instagram (reels)", InstagramScraper(), content_type="reels")
    test_platform("TikTok", TikTokScraper())
