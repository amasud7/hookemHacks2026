"""Seed the content pool with demo target videos from TikTok and Instagram."""

import json
from dataclasses import asdict

from scrapers import TikTokScraper, InstagramScraper, ScraperResult

DEMO_QUERIES = {
    "sopranos_oooh": [
        "sopranos oooh",
        "sopranos ohh",
        "sopranos gabagool",
    ],
    "monkey_finger": [
        "monkey finger in mouth",
        "monkey finger meme",
    ],
    "speed_laugh": [
        "speed trying not to laugh",
        "ishowspeed try not to laugh",
    ],
}

MAX_RESULTS_PER_QUERY = 20
OUTPUT_FILE = "content_pool.json"


def scrape_demo_content() -> list[dict]:
    tt = TikTokScraper()
    ig = InstagramScraper()

    all_results: list[ScraperResult] = []
    seen_urls: set[str] = set()

    for demo_name, queries in DEMO_QUERIES.items():
        demo_count = 0

        for query in queries:
            print(f"\n[{demo_name}] Searching TikTok: '{query}'...")
            try:
                tt_results = tt.search(query, max_results=MAX_RESULTS_PER_QUERY)
                for r in tt_results:
                    if r.url and r.url not in seen_urls:
                        seen_urls.add(r.url)
                        all_results.append(r)
                        demo_count += 1
                print(f"  Got {len(tt_results)} results")
            except Exception as e:
                print(f"  TikTok error: {e}")

            for ig_type in ["reels", "posts"]:
                print(f"[{demo_name}] Searching Instagram {ig_type}: '{query}'...")
                try:
                    ig_results = ig.search(query, max_results=MAX_RESULTS_PER_QUERY, content_type=ig_type)
                    for r in ig_results:
                        if r.url and r.url not in seen_urls:
                            seen_urls.add(r.url)
                            all_results.append(r)
                            demo_count += 1
                    print(f"  Got {len(ig_results)} results")
                except Exception as e:
                    print(f"  Instagram {ig_type} error: {e}")

        print(f"\n>>> {demo_name}: {demo_count} unique results")

    return [asdict(r) for r in all_results]


if __name__ == "__main__":
    print("Seeding content pool for demo...")
    pool = scrape_demo_content()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(pool, f, indent=2, default=str)

    print(f"\nDone! Saved {len(pool)} results to {OUTPUT_FILE}")
