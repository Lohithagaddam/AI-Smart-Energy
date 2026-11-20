import sqlite3
import os

# Database location
DATABASE_PATH = os.path.join("database", "energy.db")


def get_connection():
    """Create and return a connection to the SQLite database."""
    os.makedirs("database", exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create all database tables using schema.sql."""

    connection = get_connection()

    # Read schema file from the database folder
    with open("database/schema.sql", "r", encoding="utf-8") as file:
        schema = file.read()

    # Create tables
    connection.executescript(schema)
    connection.commit()

    # Check which tables were created
    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    connection.close()

    print("Database initialized successfully!")
    print("Tables created:")

    for table in tables:
        print("-", table["name"])


if __name__ == "__main__":
    initialize_database()