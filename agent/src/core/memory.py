import sqlite3
import os
import time

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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_trash(
            email_id TEXT PRIMARY KEY,
            trash_at REAL)''')
    
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

def schedule_for_trash(email_id, delay_minute=60):
    """Savses the email ID to be trashed later"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    trash_at = time.time() + (delay_minute * 60)
    try:
        cursor.execute('''
            INSERT INTO scheduled_trash (email_id, trash_at)
            VALUES (?, ?)''', (email_id, trash_at))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def get_emails_ready_to_trash():
    """Finds all emails whose wait time is over"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    current_time = time.time()
    cursor.execute('SELECT email_id FROM scheduled_trash WHERE trash_at <= ?', (current_time,))
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]

def remove_from_scheduled_trash(email_id):
    """Removes the email from waiting room after it is successfully trashed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scheduled_trash WHERE email_id = ?', (email_id,))
    conn.commit()
    conn.close()  