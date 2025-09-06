import psycopg2
from config import DB_CONFIG
from embedding_service import generate_embeddings

# --- Configuration ---
BATCH_SIZE = 100  # Process 100 guidelines at a time


def _get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
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


def persist_embeddings():
    """
    Finds all guidelines without a vector embedding, generates embeddings for them,
    and stores the results in the database.
    """
    print("Starting embedding persistence process...")
    conn = _get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            guidelines_to_process = _get_guidelines_without_embeddings(cursor)
            if not guidelines_to_process:
                print("No new guidelines to embed. All guidelines are up to date.")
                return

            print(f"Found {len(guidelines_to_process)} guidelines to embed.")
            total_processed = 0
            for i in range(0, len(guidelines_to_process), BATCH_SIZE):
                batch = guidelines_to_process[i : i + BATCH_SIZE]
                texts_to_embed = [_generate_composite_text(g) for g in batch]

                print(f"  - Generating embeddings for batch {i // BATCH_SIZE + 1}...")
                embeddings = generate_embeddings(
                    texts=texts_to_embed,
                    task_type="RETRIEVAL_DOCUMENT",
                    title="Investment Guideline Embedding",
                )

                if not embeddings:
                    print("  - Failed to generate embeddings for this batch. Skipping.")
                    continue

                updates = [(g[0], g[1], emb) for g, emb in zip(batch, embeddings)]

                print(f"  - Storing {len(updates)} new embeddings in the database...")
                _update_embeddings_in_db(cursor, updates)

                total_processed += len(batch)
                print(f"  - Progress: {total_processed}/{len(guidelines_to_process)}")

            conn.commit()
            print("\nEmbedding persistence successful. Changes have been committed.")

    except Exception as e:
        print(f"An error occurred during embedding persistence: {e}")
        conn.rollback()
    finally:
        conn.close()
