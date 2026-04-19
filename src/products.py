"""Video frame product analysis: identify products via Gemini vision, find listings via SerpAPI."""

import json

from google import genai
from google.genai import types
from serpapi import GoogleSearch

from src.config import GOOGLE_API_KEY, SERPAPI_API_KEY

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def identify_products(image_bytes: bytes, mime_type: str = "image/jpeg") -> list[dict]:
    """Use Gemini vision to identify purchasable products in an image frame.

    Returns a list of dicts: [{"name": "...", "search_query": "..."}]
    """
    client = _get_client()

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            """Analyze this image and identify all purchasable products visible.
For each product, provide:
- "name": a short, human-readable product name
- "search_query": a Google Shopping search query that would find this exact product

Focus on: clothing, shoes, accessories, electronics, furniture, food/drinks, beauty products.
Ignore: people, backgrounds, text overlays.

Return ONLY a JSON array. If no products are found, return [].
Example: [{"name": "White Nike Air Force 1", "search_query": "Nike Air Force 1 07 white"}]""",
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    try:
        products = json.loads(response.text)
        if isinstance(products, list):
            return products
    except (json.JSONDecodeError, TypeError):
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
