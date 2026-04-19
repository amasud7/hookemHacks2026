from groq import Groq
from src.config import GROQ_API_KEY

VALID_INTENTS = {"describe", "reenact", "vibe", "quote"}

_client = None

_CLASSIFY_PROMPT = """Classify this short-form content search query into exactly ONE category.

Categories:
- describe: User describes what they SAW in the video (actions, scenes, objects, people). Example: "that video where the cat jumps into the pool"
- reenact: User mimics or references AUDIO — sounds, music, sound effects, humming. Example: "the one that goes dun dun dun" or "that song that goes lovee meee"
- quote: User quotes specific DIALOGUE or TEXT overlays from the content. Example: "the one where he says get out of my room"
- vibe: User describes an EMOTION, aesthetic, or feeling — not specific content. Example: "cozy autumn rainy day video" or "that unhinged energy video"

Reply with ONLY the category name (describe, reenact, vibe, or quote). Nothing else.

Query: "{query}"
"""


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def classify_query(query: str) -> str:
    """Classify a search query into an intent preset using Groq.

    Returns one of: "describe", "reenact", "vibe", "quote".
    Falls back to "describe" on any error.
    """
    try:
        response = _get_client().chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": _CLASSIFY_PROMPT.format(query=query)}],
            max_tokens=10,
        )
        intent = response.choices[0].message.content.strip().lower().split()[0]
        if intent in VALID_INTENTS:
            return intent
        return "describe"
    except Exception:
        return "describe"
