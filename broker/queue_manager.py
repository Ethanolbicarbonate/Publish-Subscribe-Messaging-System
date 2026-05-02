"""
Queue Manager.
Bridges the Broker's domain objects (Messages) with the raw SQLite persistence layer.
"""

import json
from typing import List, Tuple
from common.message import Message
from common.constants import STATUS_PENDING, STATUS_DELIVERED, STATUS_DEAD_LETTER
from persistence import db

class QueueManager:
    """Manages the durable message queue for all subscribers."""
    
    def __init__(self):
        db.init_db()

    def enqueue_for_subscriber(self, message: Message, subscriber_id: str) -> None:
        """Saves a published message to the durable queue for a specific subscriber."""
        db.insert_message(
            msg_id=message.msg_id,
            topic=message.topic,
            payload=message.payload,
            timestamp=message.timestamp,
            subscriber_id=subscriber_id,
            status=STATUS_PENDING
        )

    def get_pending_messages(self, subscriber_id: str) -> List[Message]:
        """Retrieves all pending messages for a subscriber as Message objects."""
        rows = db.get_messages_by_status(subscriber_id, STATUS_PENDING)
        messages = []
        for row in rows:
            msg = Message(
                type="PUBLISH",  # Reconstruct as a publish message
                topic=row['topic'],
                payload=json.loads(row['payload']),
                msg_id=row['msg_id'],
                timestamp=row['timestamp']
            )
            messages.append(msg)
        return messages

    def mark_delivered(self, msg_id: str, subscriber_id: str) -> None:
        """
        Marks a message as delivered, which can be implemented as either a status update or a deletion.
        """
        db.update_status(msg_id, subscriber_id, STATUS_DELIVERED)
        # Alternatively: db.delete_message(msg_id, subscriber_id)

    def mark_dead_letter(self, msg_id: str, subscriber_id: str) -> None:
        """Marks a message as a dead letter after exhausting retries."""
        db.update_status(msg_id, subscriber_id, STATUS_DEAD_LETTER)

    def record_retry(self, msg_id: str, subscriber_id: str) -> int:
        """Increments the retry counter and returns the new count."""
        return db.increment_retry(msg_id, subscriber_id)