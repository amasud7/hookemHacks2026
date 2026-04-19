from src.embeddings import _get_client

VALID_INTENTS = {"describe", "reenact", "vibe", "quote"}

_CLASSIFY_PROMPT = """Classify this short-form content search query into exactly ONE category.

Categories:
- describe: User describes what they SAW in the video (actions, scenes, objects, people). Example: "that video where the cat jumps into the pool"
- reenact: User mimics or references AUDIO — sounds, music, sound effects, humming. Example: "the one that goes dun dun dun" or "that song that goes lovee meee"
- quote: User quotes specific DIALOGUE or TEXT overlays from the content. Example: "the one where he says get out of my room"
- vibe: User describes an EMOTION, aesthetic, or feeling — not specific content. Example: "cozy autumn rainy day video" or "that unhinged energy video"

Reply with ONLY the category name (describe, reenact, vibe, or quote). Nothing else.

Query: "{query}"
"""


def classify_query(query: str) -> str:
    """Classify a search query into an intent preset.

    Returns one of: "describe", "reenact", "vibe", "quote".
    Falls back to "describe" on any error (most common query type).
    """
    try:
        result = _get_client().models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=_CLASSIFY_PROMPT.format(query=query),
        )
        intent = result.text.strip().lower().split()[0]  # Take first word only
        if intent in VALID_INTENTS:
            return intent
        return "describe"
    except Exception:
        return "describe"
