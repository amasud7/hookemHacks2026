"""Scrape metadata for specific demo content URLs via Apify."""

import json
from dataclasses import asdict

from scrapers import InstagramScraper, TikTokScraper

DEMO_CONTENT = {
    "sopranos_ohhh": "https://www.instagram.com/reel/DFIaEarNVA9/",
    "cats_dancing_dryer": "https://www.instagram.com/reel/DWyoxiCDGKg/",
    "6_ai_5_parachutes": "https://www.instagram.com/reel/DUn6HCeE4by/",
    "whip_for_claude_code": "https://www.instagram.com/reel/DW7u1kPDc5Z/",
    "cat_doing_scuba": "https://www.instagram.com/reel/DXOCjsnDMMd/",
    "wilson_lo_siento": "https://www.instagram.com/reel/DU3rGLLDoVX/",
    "motorcycle_scuba": "https://www.instagram.com/p/DW_0ut8jpp-/",
    "nickwilde_scuba": "https://www.instagram.com/p/DWdlzFqDFS5/",
    "charles_scuba": "https://www.instagram.com/p/DXNQSHQksVC/",
    "speed_jump1": "https://www.instagram.com/p/DXSnF_lCOb9/",
    "speed_jump2": "https://www.instagram.com/p/C-Oe7MjNqd6/",
    "speed_jump3": "https://www.instagram.com/p/DTbI_Vjjdsx/",
    "point_eye": "https://www.instagram.com/p/DNYGxHCJ7Zr/",
}

OUTPUT_FILE = "content_pool.json"


def main():
    ig_urls = [url for url in DEMO_CONTENT.values() if "instagram.com" in url]
    tt_urls = [url for url in DEMO_CONTENT.values() if "tiktok.com" in url]

    all_results = []

    if ig_urls:
        print(f"Scraping {len(ig_urls)} Instagram URLs...")
        ig = InstagramScraper()
        try:
            results = ig.scrape_urls(ig_urls)
            all_results.extend(results)
            print(f"  Got {len(results)} results")
        except Exception as e:
            print(f"  Instagram error: {e}")

    if tt_urls:
        print(f"Scraping {len(tt_urls)} TikTok URLs...")
        tt = TikTokScraper()
        try:
            results = tt.scrape_urls(tt_urls)
            all_results.extend(results)
            print(f"  Got {len(results)} results")
        except Exception as e:
            print(f"  TikTok error: {e}")

    pool = [asdict(r) for r in all_results]

    with open(OUTPUT_FILE, "w") as f:
        json.dump(pool, f, indent=2, default=str)

    print(f"\nDone! Saved {len(pool)} results to {OUTPUT_FILE}")

    # Summary
    for r in all_results:
        print(f"\n[{r.platform}] @{r.author}")
        print(f"  {r.text[:100]}{'...' if len(r.text) > 100 else ''}")
        print(f"  sound: {r.sound_name}")
        print(f"  url: {r.url}")


if __name__ == "__main__":
    main()
