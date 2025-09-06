import json
import psycopg2
from config import DB_CONFIG
from embedding_service import generate_embeddings


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to the database: {e}")
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

    cursor.execute(base_query, params)
    return cursor.fetchall()


def query_guidelines(
    query: str, portfolio_id: str = None, top_k: int = 5, raw_output: bool = False
):
    """
    Performs a semantic search for guidelines based on a query.
    Optionally filters by portfolio.
    If raw_output is True, returns a JSON string of the results.
    """
    if not raw_output:
        print(f"Generating embedding for your query: '{query}'...")

    embeddings = generate_embeddings(texts=[query], task_type="RETRIEVAL_QUERY")
    if not embeddings:
        if not raw_output:
            print("Could not generate query embedding. Aborting.")
        return None
    query_embedding = embeddings[0]

    conn = get_db_connection()
    if not conn:
        return None

    results = []
    try:
        with conn.cursor() as cursor:
            if not raw_output:
                print("Searching for similar guidelines...")
            results = find_similar_guidelines(
                cursor, query_embedding, portfolio_id, top_k
            )
    except Exception as e:
        if not raw_output:
            print(f"An error occurred during the database query: {e}")
    finally:
        conn.close()

    if raw_output:
        guideline_list = []
        for row in results:
            text, provenance, page, portfolio_name, similarity = row
            guideline_list.append(
                {
                    "portfolio_name": portfolio_name,
                    "guideline_text": text,
                    "provenance": provenance,
                    "page": page,
                    "similarity": similarity,
                }
            )
        return json.dumps(guideline_list, indent=2)
    else:
        return results
