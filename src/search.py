from src.db import get_collection
from src.embeddings import embed_query
from src.models import SearchResult
from src.config import VECTOR_INDEX_NAME

# Modality weight presets for different query types
QUERY_PRESETS = {
    "describe": {"text": 1.0, "visual": 1.5, "audio": 0.3, "description": 1.5},
    "reenact":  {"text": 0.3, "visual": 0.5, "audio": 2.0, "description": 0.3},
    "vibe":     {"text": 1.0, "visual": 1.0, "audio": 1.0, "description": 1.0},
    "quote":    {"text": 2.0, "visual": 0.3, "audio": 0.5, "description": 0.5},
    "default":  {"text": 1.0, "visual": 1.0, "audio": 1.0, "description": 1.0},
}


def _vector_search_pipeline(
    path: str,
    query_vector: list[float],
    limit: int,
    num_candidates: int,
    filters: dict | None = None,
) -> list[dict]:
    """Run a single $vectorSearch aggregation against one embedding field."""
    stage: dict = {
        "$vectorSearch": {
            "index": VECTOR_INDEX_NAME,
            "path": path,
            "queryVector": query_vector,
            "numCandidates": num_candidates,
            "limit": limit,
        }
    }
    if filters:
        stage["$vectorSearch"]["filter"] = filters

    pipeline = [
        stage,
        {
            "$project": {
                "_id": 0,
                "content_id": 1,
                "platform": 1,
                "url": 1,
                "creator": 1,
                "caption": 1,
                "thumb": 1,
                "video_url": 1,
                "likes": 1,
                "views": 1,
                "comments": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    collection = get_collection()
    return list(collection.aggregate(pipeline))


def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    weights: list[float],
    k: int = 60,
) -> list[dict]:
    """Combine multiple ranked result lists using weighted Reciprocal Rank Fusion.

    RRF score for a document = sum over lists of: weight * 1/(k + rank + 1)
    Higher k dampens the effect of rank differences.
    """
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for results, weight in zip(result_lists, weights):
        for rank, doc in enumerate(results):
            doc_id = doc["content_id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + weight * (1.0 / (k + rank + 1))
            # Keep the doc data (latest version wins, but they should be identical)
            docs[doc_id] = doc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{**docs[doc_id], "score": score} for doc_id, score in ranked]


def search(
    query: str = "",
    query_vector: list[float] | None = None,
    text_query_vector: list[float] | None = None,
    audio_query_vector: list[float] | None = None,
    preset: str = "default",
    weights: dict[str, float] | None = None,
    limit: int = 10,
    platform: str | None = None,
) -> list[SearchResult]:
    """Search content across all modalities using per-modality vector search + RRF.

    Args:
        query: Natural language search query (used if query_vector not provided)
        query_vector: Default embedding vector used for all modalities
        text_query_vector: Override vector for text_embedding search (e.g. from audio transcript)
        audio_query_vector: Override vector for audio_embedding search (e.g. raw audio waveform)
        preset: One of QUERY_PRESETS keys ("describe", "reenact", "vibe", "quote", "default")
        weights: Custom weights dict {"text": float, "visual": float, "audio": float}.
                 Overrides preset if provided.
        limit: Number of results to return
        platform: Optional platform filter ("tiktok", "instagram", "youtube")
    """
    w = weights if weights is not None else QUERY_PRESETS.get(preset, QUERY_PRESETS["default"])
    if query_vector is None:
        if not query:
            raise ValueError("Either query or query_vector must be provided")
        query_vector = embed_query(query)
    num_candidates = limit * 15  # oversample for better recall

    filters = {}
    if platform:
        filters["platform"] = {"$eq": platform}

    # Run 3 separate vector searches, using per-modality vectors when available
    text_results = _vector_search_pipeline(
        path="text_embedding",
        query_vector=text_query_vector or query_vector,
        limit=limit,
        num_candidates=num_candidates,
        filters=filters or None,
    )

    visual_results = _vector_search_pipeline(
        path="visual_embedding",
        query_vector=query_vector,
        limit=limit,
        num_candidates=num_candidates,
        filters=filters or None,
    )

    audio_filters = {**(filters or {}), "has_audio": {"$eq": True}}
    audio_results = _vector_search_pipeline(
        path="audio_embedding",
        query_vector=audio_query_vector or query_vector,
        limit=limit,
        num_candidates=num_candidates,
        filters=audio_filters,
    )

    description_results = _vector_search_pipeline(
        path="description_embedding",
        query_vector=query_vector,
        limit=limit,
        num_candidates=num_candidates,
        filters=filters or None,
    )

    # Combine with weighted RRF
    fused = reciprocal_rank_fusion(
        result_lists=[text_results, visual_results, audio_results, description_results],
        weights=[w["text"], w["visual"], w["audio"], w.get("description", 1.0)],
    )

    return [SearchResult(**doc) for doc in fused[:limit]]
