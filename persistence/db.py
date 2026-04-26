"""
Raw SQLite database operations for message persistence.
Ensures durable storage using a normalized schema to minimize I/O and storage footprint.
"""

import sqlite3
import json
from typing import List, Dict, Any
from common.constants import DB_PATH, STATUS_PENDING

def _get_connection() -> sqlite3.Connection:
    """Returns a fresh database connection. Safe for multi-threaded use."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row 
    # Enable foreign keys for SQLite
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db() -> None:
    """Initializes the normalized database schema."""
    with _get_connection() as conn:
        # Table 1: Stores the heavy, immutable payload only once
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                msg_id TEXT PRIMARY KEY,
                topic TEXT,
                payload TEXT,
                timestamp TEXT
            )
        """)
        # Table 2: Maps subscribers to message states (junction table)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS delivery_status (
                msg_id TEXT,
                subscriber_id TEXT,
                status TEXT,
                retry_count INTEGER DEFAULT 0,
                PRIMARY KEY (msg_id, subscriber_id),
                FOREIGN KEY (msg_id) REFERENCES messages(msg_id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    print("[DB] Normalized SQLite database initialized successfully.")

def insert_message(msg_id: str, topic: str, payload: Dict[str, Any], 
                   timestamp: str, subscriber_id: str, status: str = STATUS_PENDING) -> None:
    """Inserts a message and updates the subscriber delivery state."""
    with _get_connection() as conn:
        # INSERT OR IGNORE ensures the heavy payload is only written once per msg_id
        conn.execute("""
            INSERT OR IGNORE INTO messages 
            (msg_id, topic, payload, timestamp)
            VALUES (?, ?, ?, ?)
        """, (msg_id, topic, json.dumps(payload), timestamp))
        
        # Track the delivery state for this specific subscriber
        conn.execute("""
            INSERT OR IGNORE INTO delivery_status 
            (msg_id, subscriber_id, status, retry_count)
            VALUES (?, ?, ?, 0)
        """, (msg_id, subscriber_id, status))
        conn.commit()

def get_messages_by_status(subscriber_id: str, status: str) -> List[sqlite3.Row]:
    """Retrieves all messages for a subscriber via a JOIN."""
    with _get_connection() as conn:
        cursor = conn.execute("""
            SELECT m.msg_id, m.topic, m.payload, m.timestamp, d.status, d.retry_count, d.subscriber_id 
            FROM messages m
            JOIN delivery_status d ON m.msg_id = d.msg_id
            WHERE d.subscriber_id = ? AND d.status = ?
            ORDER BY m.timestamp ASC
        """, (subscriber_id, status))
        return cursor.fetchall()

def update_status(msg_id: str, subscriber_id: str, new_status: str) -> None:
    """Updates the delivery status of a specific message for a subscriber."""
    with _get_connection() as conn:
        conn.execute("""
            UPDATE delivery_status SET status = ? 
            WHERE msg_id = ? AND subscriber_id = ?
        """, (new_status, msg_id, subscriber_id))
        conn.commit()

def increment_retry(msg_id: str, subscriber_id: str) -> int:
    """Increments the retry count and returns the new count."""
    with _get_connection() as conn:
        conn.execute("""
            UPDATE delivery_status SET retry_count = retry_count + 1 
            WHERE msg_id = ? AND subscriber_id = ?
        """, (msg_id, subscriber_id))
        conn.commit()
        
        cursor = conn.execute("""
            SELECT retry_count FROM delivery_status 
            WHERE msg_id = ? AND subscriber_id = ?
        """, (msg_id, subscriber_id))
        row = cursor.fetchone()
        return row['retry_count'] if row else 0

def delete_message(msg_id: str, subscriber_id: str) -> None:
    """Removes a message status, and cleans up the payload if orphaned."""
    with _get_connection() as conn:
        conn.execute("""
            DELETE FROM delivery_status 
            WHERE msg_id = ? AND subscriber_id = ?
        """, (msg_id, subscriber_id))
        
        # Cleanup payload if no subscribers need this message anymore
        conn.execute("""
            DELETE FROM messages
            WHERE msg_id = ? AND NOT EXISTS (
                SELECT 1 FROM delivery_status WHERE msg_id = ?
            )
        """, (msg_id, msg_id))
        conn.commit()