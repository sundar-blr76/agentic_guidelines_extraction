import psycopg2
from .config import DB_CONFIG
from .embedding_service import generate_embeddings
from typing import Dict, Any

# --- Configuration ---
BATCH_SIZE = 100  # Process 100 guidelines at a time


def _get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        # For the API, we'll let the calling function handle the error.
        # For the CLI, this print is still useful.
        print(f"Error: Could not connect to the database: {e}")
        return None


def _get_guidelines_without_embeddings(cursor):
    """Fetches guidelines that do not have an embedding yet."""
    query = """
        SELECT g.portfolio_id, g.rule_id, p.portfolio_name, g.part, g.section, g.subsection, g.text
        FROM guideline g
        JOIN portfolio p ON g.portfolio_id = p.portfolio_id
        WHERE g.embedding IS NULL;
    """
    cursor.execute(query)
    return cursor.fetchall()


def _generate_composite_text(guideline):
    """Creates a single string from guideline data for embedding."""
    portfolio_name, part, section, subsection, text = (
        guideline[2],
        guideline[3],
        guideline[4],
        guideline[5],
        guideline[6],
    )
    return f"Portfolio: {portfolio_name}; Part: {part or 'N/A'}; Section: {section or 'N/A'}; Subsection: {subsection or 'N/A'}; Guideline: {text}"


def _update_embeddings_in_db(cursor, updates):
    """Updates the database with the newly generated embeddings."""
    update_query = (
        "UPDATE guideline SET embedding = %s WHERE portfolio_id = %s AND rule_id = %s;"
    )
    for portfolio_id, rule_id, embedding in updates:
        cursor.execute(update_query, (embedding, portfolio_id, rule_id))


def stamp_missing_embeddings() -> Dict[str, Any]:
    """
    Core logic to find, generate, and store embeddings for guidelines.
    Designed to be called from an API. Returns a status dictionary.
    """
    conn = _get_db_connection()
    if not conn:
        return {"status": "error", "message": "Database connection failed."}

    try:
        with conn.cursor() as cursor:
            guidelines_to_process = _get_guidelines_without_embeddings(cursor)
            if not guidelines_to_process:
                return {
                    "status": "no_action",
                    "message": "No new guidelines to embed. All guidelines are up to date.",
                }

            total_found = len(guidelines_to_process)
            total_processed = 0
            for i in range(0, len(guidelines_to_process), BATCH_SIZE):
                batch = guidelines_to_process[i : i + BATCH_SIZE]
                texts_to_embed = [_generate_composite_text(g) for g in batch]

                embeddings = generate_embeddings(
                    texts=texts_to_embed,
                    task_type="RETRIEVAL_DOCUMENT",
                    title="Investment Guideline Embedding",
                )

                if not embeddings:
                    # Log this failure for the batch but try to continue
                    continue

                updates = [(g[0], g[1], emb) for g, emb in zip(batch, embeddings)]
                _update_embeddings_in_db(cursor, updates)
                total_processed += len(updates)

            conn.commit()
            return {
                "status": "success",
                "total_found": total_found,
                "processed_count": total_processed,
            }

    except Exception as e:
        if conn:
            conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        if conn:
            conn.close()


def persist_embeddings():
    """
    CLI wrapper for the embedding persistence process.
    Handles printing status to the console.
    """
    print("Starting embedding persistence process...")
    result = stamp_missing_embeddings()

    if result["status"] == "error":
        print(f"An error occurred: {result['message']}")
    elif result["status"] == "no_action":
        print(result["message"])
    elif result["status"] == "success":
        print(f"Found {result['total_found']} guidelines to process.")
        print(f"Successfully generated and stored {result['processed_count']} embeddings.")
        if result['total_found'] != result['processed_count']:
            print(f"Warning: Failed to process {result['total_found'] - result['processed_count']} guidelines.")
        print("Embedding persistence successful. Changes have been committed.")
