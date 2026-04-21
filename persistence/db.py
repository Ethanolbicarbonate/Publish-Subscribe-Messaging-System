"""
Raw SQLite database operations for message persistence.
Ensures durable storage of fanned-out messages per subscriber.
"""

import sqlite3
import json
from typing import List, Dict, Any
from common.constants import DB_PATH, STATUS_PENDING

def _get_connection() -> sqlite3.Connection:
    """Returns a fresh database connection. Safe for multi-threaded use."""
    # timeout=10 allows multiple threads to wait for the DB lock instead of immediately failing
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row  # Returns dict-like rows instead of tuples
    return conn

def init_db() -> None:
    """Initializes the database schema."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                msg_id TEXT,
                topic TEXT,
                payload TEXT,
                timestamp TEXT,
                status TEXT,
                retry_count INTEGER DEFAULT 0,
                subscriber_id TEXT,
                PRIMARY KEY (msg_id, subscriber_id)
            )
        """)
        conn.commit()
    print("[DB] SQLite database initialized successfully.")

def insert_message(msg_id: str, topic: str, payload: Dict[str, Any], 
                   timestamp: str, subscriber_id: str, status: str = STATUS_PENDING) -> None:
    """Inserts a new message destined for a specific subscriber."""
    with _get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO messages 
            (msg_id, topic, payload, timestamp, status, retry_count, subscriber_id)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (msg_id, topic, json.dumps(payload), timestamp, status, subscriber_id))
        conn.commit()

def get_messages_by_status(subscriber_id: str, status: str) -> List[sqlite3.Row]:
    """Retrieves all messages for a subscriber currently in the given status."""
    with _get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM messages 
            WHERE subscriber_id = ? AND status = ?
            ORDER BY timestamp ASC
        """, (subscriber_id, status))
        return cursor.fetchall()

def update_status(msg_id: str, subscriber_id: str, new_status: str) -> None:
    """Updates the delivery status of a specific message for a subscriber."""
    with _get_connection() as conn:
        conn.execute("""
            UPDATE messages SET status = ? 
            WHERE msg_id = ? AND subscriber_id = ?
        """, (new_status, msg_id, subscriber_id))
        conn.commit()

def increment_retry(msg_id: str, subscriber_id: str) -> int:
    """Increments the retry count and returns the new count."""
    with _get_connection() as conn:
        conn.execute("""
            UPDATE messages SET retry_count = retry_count + 1 
            WHERE msg_id = ? AND subscriber_id = ?
        """, (msg_id, subscriber_id))
        conn.commit()
        
        cursor = conn.execute("""
            SELECT retry_count FROM messages 
            WHERE msg_id = ? AND subscriber_id = ?
        """, (msg_id, subscriber_id))
        row = cursor.fetchone()
        return row['retry_count'] if row else 0

def delete_message(msg_id: str, subscriber_id: str) -> None:
    """Removes a message from the queue (e.g., after successful delivery)."""
    with _get_connection() as conn:
        conn.execute("""
            DELETE FROM messages 
            WHERE msg_id = ? AND subscriber_id = ?
        """, (msg_id, subscriber_id))
        conn.commit()