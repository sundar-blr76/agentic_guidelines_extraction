import psycopg2
from config import DB_CONFIG


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to the database: {e}")
        return None


def execute_schema(cursor, schema_path="schema.sql"):
    """Reads and executes the SQL schema file."""
    print(f"Reading schema from '{schema_path}'...")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    print("Executing schema to drop and recreate tables...")
    cursor.execute(schema_sql)
    print("Schema executed successfully.")


def main():
    """Main function to set up the database."""
    print("Starting database setup...")
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            execute_schema(cursor)

        conn.commit()
        print("Database setup successful. Changes have been committed.")

    except Exception as e:
        print(f"An error occurred during database setup: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
