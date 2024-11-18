import sqlite3

# Connect to SQLite (or create a new database if it doesn't exist)
conn = sqlite3.connect("my_database.db")

# Create a cursor to interact with the database
cursor = conn.cursor()

# Example: Create a table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")
conn.commit()

# Close the connection when done
conn.close()
