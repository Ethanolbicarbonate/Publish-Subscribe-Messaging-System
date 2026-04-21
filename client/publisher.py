"""
Publisher Client.
Inherits from BaseClient and provides a simple API to publish messages
to specific topics.
"""

from typing import Dict, Any, Optional
from client.base_client import BaseClient
from common.message import Message
from common.constants import TYPE_PUBLISH

class Publisher(BaseClient):
    """
    Client responsible for publishing messages to the broker.
    Handles network resilience automatically via BaseClient.
    """
    def __init__(self, client_id: Optional[str] = None):
        super().__init__(client_id)

    def publish(self, topic: str, payload: Dict[str, Any]) -> bool:
        """
        Creates a PUBLISH message and sends it to the broker.
        The Message dataclass automatically generates a UUID and timestamp.
        
        Args:
            topic (str): The routing topic (e.g., 'STOCK.AAPL')
            payload (dict): The data to send.
            
        Returns:
            bool: True if the message was successfully queued for sending over the socket.
        """
        msg = Message(
            type=TYPE_PUBLISH,
            topic=topic,
            payload=payload
        )
        print(f"[Publisher {self.client_id}] Publishing to '{topic}': {payload}")
        return self.send(msg)

# --- Quick Test / Usage Example ---
if __name__ == "__main__":
    import time
    
    # Initialize and connect the publisher
    pub = Publisher()
    pub.start()
    
    # Wait a brief moment to ensure the connection and handshake complete
    time.sleep(1)
    
    if pub.connected:
        pub.publish("STOCK.AAPL", {"price": 150.25, "volume": 1000})
        time.sleep(1) # Wait for network transmission before exiting
        
    pub.stop()