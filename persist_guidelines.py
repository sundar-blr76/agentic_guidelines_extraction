import json
import psycopg2
from psycopg2 import sql
from config import DB_CONFIG
from typing import Dict, Any


def get_db_connection():
    """Est-ablishes a connection to the PostgreSQL database using config.py."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        # In a library/API context, raising an exception is often better than printing.
        # However, for the CLI, printing is user-friendly. We'll keep it for now.
        print(
            "Error: Could not connect to the database. Please check your connection settings in config.py."
        )
        print(f"Details: {e}")
        return None


def _delete_portfolio_if_exists(cursor, portfolio_id) -> bool:
    """Deletes a portfolio and all its related data if it already exists."""
    cursor.execute("SELECT 1 FROM portfolio WHERE portfolio_id = %s;", (portfolio_id,))
    if cursor.fetchone():
        cursor.execute(
            "DELETE FROM portfolio WHERE portfolio_id = %s;", (portfolio_id,)
        )
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


def persist_guidelines_from_data(
    data: Dict[str, Any], human_readable_digest: str
) -> Dict[str, Any]:
    """
    Performs the core logic of ingesting parsed data into the database.
    This function is designed to be called from an API or other modules.
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "message": "Database connection failed."}

    try:
        with conn.cursor() as cursor:
            portfolio_id = data["portfolio_id"]

            was_deleted = _delete_portfolio_if_exists(cursor, portfolio_id)

            _ingest_portfolio(cursor, data)
            _ingest_document(cursor, data, human_readable_digest)
            _ingest_guidelines(
                cursor, portfolio_id, data["doc_id"], data["guidelines"]
            )

            conn.commit()

            return {
                "status": "success",
                "portfolio_id": portfolio_id,
                "doc_id": data["doc_id"],
                "ingested_guidelines": len(data["guidelines"]),
                "was_reingested": was_deleted,
            }

    except Exception as e:
        if conn:
            conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        if conn:
            conn.close()


def persist_guidelines_from_file(json_path: str):
    """
    CLI wrapper that reads a JSON file and persists its data into the database.
    Handles file I/O and prints progress to the console.
    """
    print(f"Starting persistence for: {json_path}")

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

    # Call the core logic function
    result = persist_guidelines_from_data(data, human_readable_digest)

    # Print the results to the console
    if result["status"] == "success":
        print(f"  - Portfolio '{result['portfolio_id']}' processed.")
        if result["was_reingested"]:
            print("  - Existing data was deleted and re-persisted.")
        print(f"  - Persisted document: {result['doc_id']}")
        print(f"  - Persisted {result['ingested_guidelines']} guidelines.")
        print("Persistence successful. All changes have been committed.")
    else:
        print(f"An error occurred during persistence: {result['message']}")
        print("Transaction has been rolled back.")
