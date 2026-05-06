"""
Administrative Tool: Dead Letter Queue Inspector
Retrieves and displays all messages that exhausted retry attempts and were marked as DEAD_LETTER.
"""

import sqlite3
import json
import os
from common.constants import DB_PATH, STATUS_DEAD_LETTER

def inspect_dead_letters():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    print(f"--- Dead Letter Inspection ---")
    print(f"Querying for status: {STATUS_DEAD_LETTER}...\n")

    cursor = conn.execute("""
        SELECT m.timestamp, m.topic, d.subscriber_id, d.retry_count, m.payload
        FROM messages m
        JOIN delivery_status d ON m.msg_id = d.msg_id
        WHERE d.status = ?
        ORDER BY m.timestamp DESC
    """, (STATUS_DEAD_LETTER,))
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No dead letters found. The queue is healthy.")
        return
        
    print(f"Found {len(rows)} dead letter(s):\n")
    for row in rows:
        print(f"Timestamp:     {row['timestamp']}")
        print(f"Topic:         {row['topic']}")
        print(f"Subscriber ID: {row['subscriber_id']}")
        print(f"Retry Count:   {row['retry_count']}")
        
        try:
            payload_data = json.loads(row['payload'])
            print("Payload:")
            print(json.dumps(payload_data, indent=2))
        except json.JSONDecodeError:
            print(f"Payload (Raw): {row['payload']}")
            
        print("-" * 40)
        
    conn.close()

if __name__ == "__main__":
    inspect_dead_letters()