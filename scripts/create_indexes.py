"""One-time script to create the vector search index programmatically.

You can also create the index via the Atlas UI — see the plan for the JSON config.
This script is an alternative for convenience.

Usage:
    python -m scripts.create_indexes
"""

from src.db import get_collection, create_vector_index


def main():
    collection = get_collection()
    print(f"Connected to {collection.database.name}.{collection.name}")
    create_vector_index(collection)
    print("Done. Check Atlas UI for index status (may take a few minutes to build).")


if __name__ == "__main__":
    main()
