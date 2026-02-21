import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DB_PATH = os.path.join(BASE_DIR, "agent_memory.db")

def init_db():
    """Creates the database and the table if they dont exist yet"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    #create a table to store processed emails
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails(
            email_id TEXT PRIMARY KEY,
            sender TEXT,
            subject TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def is_email_processed(email_id):
    """Checks the database to see if we have already read this email."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT 1 FROM processed_emails WHERE email_id = ?', (email_id,))
    result = cursor.fetchone()
    conn.close()

    return result is not None

def log_email(email_id, sender, subject):
    """Saves the email ID to the database so we dont process it again"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO processed_emails (email_id, sender, subject)
            VALUES (?, ?, ?)''', (email_id, sender, subject))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()