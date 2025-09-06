import psycopg2
from config import DB_CONFIG


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to the database: {e}")
        return None


def check_table_counts(cursor):
    """Checks and prints the row count for each table."""
    tables = ["portfolio", "document", "guideline"]
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  - Rows in '{table}': {count}")
        except psycopg2.Error as e:
            print(f"  - Could not check table '{table}': {e}")


def main():
    """Main function to verify data in the database."""
    print("Connecting to the database to verify data...")
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            check_table_counts(cursor)
    except Exception as e:
        print(f"An error occurred during verification: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
