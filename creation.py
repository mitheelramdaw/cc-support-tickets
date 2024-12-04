import sqlite3

# Create the tickets.db SQLite database and the tickets table
def create_tickets_db():
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()

    # Create the tickets table if it doesn't exist, including StatusUpdated column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ID TEXT PRIMARY KEY,
        Issue TEXT NOT NULL,
        Status TEXT NOT NULL,
        Priority TEXT NOT NULL,
        DateSubmitted TEXT NOT NULL,
        StatusUpdated TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()
    print("Database and table created successfully.")

# Run the function to create the database and table
create_tickets_db()
