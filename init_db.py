import sqlite3

def create_database():
    conn = sqlite3.connect('memory.sqlite')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Tasks (
                      id INTEGER PRIMARY KEY,
                      title TEXT,
                      description TEXT,
                      dueDate TEXT,
                      status TEXT,
                      dependencies TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ChatHistory (
                      id INTEGER PRIMARY KEY,
                      summary TEXT)''')
    conn.commit()
    conn.close()

# Call the function to create the database
create_database()
