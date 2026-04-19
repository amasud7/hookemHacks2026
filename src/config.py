import os
from dotenv import load_dotenv

load_dotenv()

# Gemini
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
EMBEDDING_MODEL = "gemini-embedding-2-preview"
EMBEDDING_DIMS = 768

# MongoDB
MONGODB_URI = os.environ.get("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "vibesearch")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "content")

# Groq (for video descriptions - fallback)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Anthropic (for video/image descriptions)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Vector search index name (single consolidated index for M0 free tier)
VECTOR_INDEX_NAME = "idx_all_embeddings"
