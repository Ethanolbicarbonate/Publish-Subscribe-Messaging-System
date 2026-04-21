"""
Data model for system messages.
Provides a standard structure for all data moving through the Pub/Sub broker.
"""

import uuid
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class Message:
    # Mandatory field for all messages
    type: str 
    # Routing topic, default empty for non-publish messages (e.g. Heartbeats)
    topic: str = ""
    # The actual data being sent
    payload: Dict[str, Any] = field(default_factory=dict)
    # Unique identifier for tracking and at-least-once delivery deduping
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # ISO8601 timestamp in UTC
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """Serializes the message properties to a Python dictionary."""
        return {
            "msg_id": self.msg_id,
            "topic": self.topic,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "type": self.type
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """Reconstructs a Message instance from a dictionary."""
        return cls(
            type=data.get("type", ""),
            topic=data.get("topic", ""),
            payload=data.get("payload", {}),
            msg_id=data.get("msg_id", ""),
            timestamp=data.get("timestamp", "")
        )