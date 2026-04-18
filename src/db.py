from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.operations import SearchIndexModel

from src.config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, VECTOR_INDEX_NAME, EMBEDDING_DIMS

_client: MongoClient | None = None


def get_collection() -> Collection:
    """Get the content collection, reusing the client connection."""
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
    return _client[MONGODB_DB][MONGODB_COLLECTION]


def create_vector_index(collection: Collection | None = None) -> None:
    """Create the consolidated vector search index with all three embedding fields.

    Safe to call multiple times — skips if the index already exists.
    """
    if collection is None:
        collection = get_collection()

    existing = [idx["name"] for idx in collection.list_search_indexes()]
    if VECTOR_INDEX_NAME in existing:
        print(f"Index '{VECTOR_INDEX_NAME}' already exists, skipping.")
        return

    index_definition = {
        "fields": [
            {
                "type": "vector",
                "path": "text_embedding",
                "numDimensions": EMBEDDING_DIMS,
                "similarity": "dotProduct",
            },
            {
                "type": "vector",
                "path": "visual_embedding",
                "numDimensions": EMBEDDING_DIMS,
                "similarity": "dotProduct",
            },
            {
                "type": "vector",
                "path": "audio_embedding",
                "numDimensions": EMBEDDING_DIMS,
                "similarity": "dotProduct",
            },
            {"type": "filter", "path": "platform"},
            {"type": "filter", "path": "content_type"},
            {"type": "filter", "path": "has_audio"},
        ]
    }

    model = SearchIndexModel(
        definition=index_definition,
        name=VECTOR_INDEX_NAME,
        type="vectorSearch",
    )
    collection.create_search_index(model=model)
    print(f"Index '{VECTOR_INDEX_NAME}' created. It may take a few minutes to become active.")
