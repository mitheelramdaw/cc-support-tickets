import sqlite3

def create_db():
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ID TEXT PRIMARY KEY,
        Issue TEXT,
        Status TEXT,
        Priority TEXT,
        DateSubmitted TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Call this function to ensure the DB exists before app starts
create_db()
