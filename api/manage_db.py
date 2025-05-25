import os
import sqlite3
from database.database import engine
from database.models import Base

DB_PATH = "hinduai.db"  # Since we're now in the api folder, we can use relative path

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

def delete_db():
    """Delete the database file if it exists."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Database file {DB_PATH} deleted successfully!")
    else:
        print("No database file found.")

def view_db():
    """View the contents of the database."""
    if not os.path.exists(DB_PATH):
        print("No database file found. Please initialize the database first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        print(f"\n=== Contents of {table_name} ===")
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in cursor.fetchall()]
        print("Columns:", ", ".join(columns))
        
        # Get table contents
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        
        if rows:
            for row in rows:
                print(row)
        else:
            print("No data in table")
        print("=" * 50)

    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python manage_db.py [init|delete|view]")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "init":
        init_db()
    elif command == "delete":
        delete_db()
    elif command == "view":
        view_db()
    else:
        print("Invalid command. Use: init, delete, or view") 