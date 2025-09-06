import json
import psycopg2
from psycopg2 import sql
from config import DB_CONFIG


def get_db_connection():
    """Establishes a connection to the PostgreSQL database using config.py."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(
            "Error: Could not connect to the database. Please check your connection settings in config.py."
        )
        print(f"Details: {e}")
        return None


def _delete_portfolio_if_exists(cursor, portfolio_id):
    """Deletes a portfolio and all its related data if it already exists."""
    cursor.execute("SELECT 1 FROM portfolio WHERE portfolio_id = %s;", (portfolio_id,))
    if cursor.fetchone():
        print(f"  - Portfolio '{portfolio_id}' already exists. Deleting old data...")
        cursor.execute(
            "DELETE FROM portfolio WHERE portfolio_id = %s;", (portfolio_id,)
        )
        print(f"  - Old data for portfolio '{portfolio_id}' deleted.")
        return True
    return False


def _ingest_portfolio(cursor, data):
    """Inserts portfolio data."""
    query = sql.SQL(
        "INSERT INTO portfolio (portfolio_id, portfolio_name) VALUES (%s, %s);"
    )
    cursor.execute(query, (data["portfolio_id"], data["portfolio_name"]))


def _ingest_document(cursor, data, human_readable_digest):
    """Inserts document data."""
    query = sql.SQL(
        "INSERT INTO document (doc_id, portfolio_id, doc_name, doc_date, human_readable_digest) VALUES (%s, %s, %s, %s, %s);"
    )
    cursor.execute(
        query,
        (
            data["doc_id"],
            data["portfolio_id"],
            data["doc_name"],
            data["doc_date"],
            human_readable_digest,
        ),
    )


def _ingest_guidelines(cursor, portfolio_id, doc_id, guidelines):
    """Inserts guideline data using the new composite key."""
    query = sql.SQL("""
        INSERT INTO guideline (portfolio_id, rule_id, doc_id, part, section, subsection, text, page, provenance, structured_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """)
    for guideline in guidelines:
        structured_data = guideline.get("structured")
        cursor.execute(
            query,
            (
                portfolio_id,
                guideline["rule_id"],
                doc_id,
                guideline.get("part"),
                guideline.get("section"),
                guideline.get("subsection"),
                guideline.get("text"),
                guideline.get("page"),
                guideline.get("provenance"),
                json.dumps(structured_data) if structured_data else None,
            ),
        )


def ingest_file(json_path: str):
    """
    Reads a JSON file and ingests its data into the database.
    If the portfolio already exists, it will be deleted and replaced.
    """
    print(f"Starting ingestion for: {json_path}")

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}")
        return

    md_path = json_path.replace(".json", ".md")
    try:
        with open(md_path, "r") as f:
            human_readable_digest = f.read()
    except FileNotFoundError:
        print(f"Warning: Markdown file not found at {md_path}. Digest will be empty.")
        human_readable_digest = ""

    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        portfolio_id = data["portfolio_id"]

        if _delete_portfolio_if_exists(cursor, portfolio_id):
            conn.commit()

        _ingest_portfolio(cursor, data)
        conn.commit()
        print(f"  - Ingested portfolio: {portfolio_id}")

        _ingest_document(cursor, data, human_readable_digest)
        conn.commit()
        print(f"  - Ingested document: {data['doc_id']}")

        _ingest_guidelines(cursor, portfolio_id, data["doc_id"], data["guidelines"])
        conn.commit()
        print(f"  - Ingested {len(data['guidelines'])} guidelines.")

        print("Ingestion successful. All changes have been committed.")

    except Exception as e:
        print(f"An error occurred during ingestion: {e}")
        if conn:
            conn.rollback()
        print("Transaction has been rolled back.")
    finally:
        if conn:
            cursor.close()
            conn.close()
