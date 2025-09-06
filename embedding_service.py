import os
import google.generativeai as genai
from typing import List

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = "models/embedding-001"


def initialize_embedding_service():
    """Initializes the connection to the embedding API."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=GEMINI_API_KEY)


def generate_embeddings(
    texts: List[str], task_type: str, title: str = None
) -> List[List[float]]:
    """
    Generates embeddings for a list of texts.

    Args:
        texts: A list of strings to embed.
        task_type: The type of task, e.g., "RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY".
        title: An optional title for document embeddings.

    Returns:
        A list of embedding vectors.
    """
    initialize_embedding_service()
    try:
        if title:
            result = genai.embed_content(
                model=EMBEDDING_MODEL, content=texts, task_type=task_type, title=title
            )
        else:
            result = genai.embed_content(
                model=EMBEDDING_MODEL, content=texts, task_type=task_type
            )
        return result["embedding"]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return []
