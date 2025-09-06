import json
import logging
from typing import List, Dict, Any
import psycopg2
from config import DB_CONFIG
from embedding_service import generate_embeddings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        logging.info("Connecting to the database...")
        conn = psycopg2.connect(**DB_CONFIG)
        logging.info("Database connection successful.")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Could not connect to the database: {e}")
        return None


def find_similar_guidelines(cursor, query_embedding, portfolio_id=None, top_k=5):
    """Finds the most similar guidelines using vector search."""
    base_query = """
        SELECT
            g.text, g.provenance, g.page, p.portfolio_name,
            1 - (g.embedding <=> %s::vector) AS similarity
        FROM guideline g
        JOIN portfolio p ON g.portfolio_id = p.portfolio_id
    """
    params = [query_embedding]

    if portfolio_id:
        base_query += " WHERE g.portfolio_id = %s"
        params.append(portfolio_id)

    base_query += " ORDER BY similarity DESC LIMIT %s;"
    params.append(top_k)

    logging.info(f"Executing query with top_k={top_k} and portfolio_id='{portfolio_id}'")
    cursor.execute(base_query, params)
    results = cursor.fetchall()
    logging.info(f"Found {len(results)} results from the database.")
    return results


def query_guidelines(
    query: str, portfolio_id: str = None, top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Performs a semantic search for guidelines and returns structured data.
    This function is designed to be called from other modules, including an API.
    It does not print to the console.
    """
    logging.info(f"Starting guideline query for: '{query}'")
    
    logging.info("Generating embeddings for the query...")
    embeddings = generate_embeddings(texts=[query], task_type="RETRIEVAL_QUERY")
    if not embeddings:
        logging.error("Failed to generate embeddings for the query.")
        return []
    query_embedding = embeddings[0]
    logging.info("Embeddings generated successfully.")

    conn = get_db_connection()
    if not conn:
        return []

    results = []
    try:
        with conn.cursor() as cursor:
            db_results = find_similar_guidelines(
                cursor, query_embedding, portfolio_id, top_k
            )
            for i, row in enumerate(db_results):
                text, provenance, page, portfolio_name, similarity = row
                result_item = {
                    "portfolio_name": portfolio_name,
                    "guideline_text": text,
                    "provenance": provenance,
                    "page": page,
                    "similarity": similarity,
                }
                logging.info(f"Processing result #{i+1}: Similarity={similarity}")
                results.append(result_item)
    except Exception as e:
        logging.error(f"An exception occurred during database query: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed.")

    logging.info(f"Query finished. Returning {len(results)} results.")
    return results

def query_guidelines_api(
    query: str, portfolio_id: str = None, top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    API wrapper for performing a semantic search for guidelines.
    """
    logging.info("API call received for query_guidelines_api.")
    return query_guidelines(query, portfolio_id, top_k)
