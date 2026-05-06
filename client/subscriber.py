"""
Subscriber Client.
Inherits from BaseClient. Handles topic subscriptions, processing incoming
messages, and sending acknowledgments (ACKs) back to the broker.
"""

from typing import Callable, Set, Optional
from client.base_client import BaseClient
from common.message import Message
from common.constants import TYPE_SUBSCRIBE, TYPE_UNSUBSCRIBE, TYPE_PUBLISH, TYPE_ACK

class Subscriber(BaseClient):
    """
    Client responsible for receiving messages from the broker.
    Automatically handles network resilience, subscription recovery, and ACKs.
    """
    def __init__(self, callback: Callable[[Message], None], client_id: Optional[str] = None):
        """
        Args:
            callback: A function taking a Message object, executed on every received PUBLISH.
            client_id: Optional persistent ID for session resumption.
        """
        super().__init__(client_id)
        self.callback = callback
        self.active_topics: Set[str] = set()

    def subscribe(self, topic: str) -> bool:
        """Subscribes to a topic pattern and updates the broker."""
        self.active_topics.add(topic)
        if self.connected:
            msg = Message(type=TYPE_SUBSCRIBE, topic=topic)
            print(f"[Subscriber {self.client_id}] Subscribing to '{topic}'")
            return self.send(msg)
        return False

    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribes from a topic pattern and updates the broker."""
        self.active_topics.discard(topic)
        if self.connected:
            msg = Message(type=TYPE_UNSUBSCRIBE, topic=topic)
            print(f"[Subscriber {self.client_id}] Unsubscribing from '{topic}'")
            return self.send(msg)
        return False

    def on_connect(self) -> None:
        """
        Hook called by BaseClient upon successful connection/reconnection.
        Re-establishes all active subscriptions with the broker to protect against
        broker restarts losing in-memory subscription state.
        """
        for topic in self.active_topics:
            msg = Message(type=TYPE_SUBSCRIBE, topic=topic)
            self.send(msg)
            
        if self.active_topics:
            print(f"[Subscriber {self.client_id}] Re-established {len(self.active_topics)} subscriptions.")

    def handle_message(self, msg: Message) -> None:
        """
        Hook called by BaseClient when a message is received.
        Processes PUBLISH messages, invokes the callback, and sends an ACK.
        """
        if msg.type == TYPE_PUBLISH:
            try:
                self.callback(msg)
            except Exception as e:
                print(f"[Subscriber {self.client_id}] Error in user callback: {e}")

            # Send Acknowledgment
            ack_msg = Message(type=TYPE_ACK, payload={"msg_id": msg.msg_id})
            self.send(ack_msg)


if __name__ == "__main__":
    import time

    def my_callback(msg: Message):
        print(f"\n---> APP RECEIVED: Topic={msg.topic}, Payload={msg.payload}")

    sub = Subscriber(callback=my_callback, client_id="TEST-SUB-01")
    sub.start()
    
    time.sleep(1)
    
    if sub.connected:
        sub.subscribe("STOCK.*")
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sub.stop()