"""Video frame product analysis: identify products via Claude vision, find listings via SerpAPI."""

import base64
import json

import anthropic
from serpapi import GoogleSearch

from src.config import ANTHROPIC_API_KEY, SERPAPI_API_KEY

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def identify_products(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[dict]:
    """Use Claude vision to identify purchasable products in an image frame.

    Returns a list of dicts: [{"name": "...", "search_query": "..."}]
    """
    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": base64.b64encode(image_bytes).decode(),
                        },
                    },
                    {
                        "type": "text",
                        "text": """Analyze this image and identify all purchasable products visible.
For each product, provide:
- "name": a short, human-readable product name
- "search_query": a Google Shopping search query that would find this exact product

Focus on: clothing, shoes, accessories, electronics, furniture, food/drinks, beauty products.
Ignore: people, backgrounds, text overlays.

Return ONLY a JSON array. If no products are found, return [].
Example: [{"name": "White Nike Air Force 1", "search_query": "Nike Air Force 1 07 white"}]""",
                    },
                ],
            }
        ],
    )

    try:
        text = response.content[0].text
        # Handle case where Claude wraps JSON in markdown code block
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1].split("```")[0]
        products = json.loads(text.strip())
        if isinstance(products, list):
            return products
    except (json.JSONDecodeError, TypeError, IndexError):
        pass
    return []


def search_products(query: str, num_results: int = 4) -> list[dict]:
    """Search Google Shopping via SerpAPI and return top listings."""
    if not SERPAPI_API_KEY:
        return []

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": num_results,
    }

    try:
        results = GoogleSearch(params).get_dict()
        listings = []
        for item in results.get("shopping_results", [])[:num_results]:
            listings.append({
                "title": item.get("title", ""),
                "price": item.get("price", ""),
                "link": item.get("link", ""),
                "thumbnail": item.get("thumbnail", ""),
                "source": item.get("source", ""),
            })
        return listings
    except Exception as e:
        print(f"SerpAPI error: {e}")
        return []


def analyze_frame(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[dict]:
    """Full pipeline: identify products in frame, then find shopping listings for each.

    Returns:
        [{"name": "...", "search_query": "...", "listings": [...]}]
    """
    products = identify_products(image_bytes, mime_type)

    for product in products:
        query = product.get("search_query", product.get("name", ""))
        product["listings"] = search_products(query)

    return products
