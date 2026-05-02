"""
Delivery Manager.
Ensures at-least-once delivery by persisting messages before sending,
tracking acknowledgments, and retrying unacknowledged messages.
"""

import threading
import time
import socket
from typing import Dict

from common.message import Message
from common.constants import RETRY_INTERVAL, MAX_RETRIES
from common.protocol import send_message
from broker.queue_manager import QueueManager

class DeliveryManager:
    def __init__(self, queue_manager: QueueManager, active_clients: Dict[str, socket.socket], clients_lock: threading.Lock):
        self.queue = queue_manager
        self.active_clients = active_clients
        self.clients_lock = clients_lock
        self.running = False
        self.retry_thread = threading.Thread(target=self._retry_loop, daemon=True)

    def start(self) -> None:
        """Starts the background retry thread."""
        self.running = True
        self.retry_thread.start()
        print("[DeliveryManager] Background retry thread started.")

    def stop(self) -> None:
        """Stops the retry thread."""
        self.running = False

    def deliver_message(self, message: Message, subscriber_id: str) -> None:
        """
        Enqueues the message to the durable store first, then attempts 
        an immediate delivery if the client is connected.
        """
        # 1. Persist the message in PENDING state (At-Least-Once guarantee)
        self.queue.enqueue_for_subscriber(message, subscriber_id)
        
        # 2. Try to send immediately if they are active
        with self.clients_lock:
            if subscriber_id in self.active_clients:
                conn = self.active_clients[subscriber_id]
                send_message(conn, message)

    def handle_ack(self, msg_id: str, subscriber_id: str) -> None:
        """Processes an acknowledgment, marking the message as delivered."""
        self.queue.mark_delivered(msg_id, subscriber_id)
        print(f"[DeliveryManager] ACK received for msg {msg_id[-6:]} from {subscriber_id}")

    def _retry_loop(self) -> None:
        """
        Background daemon that wakes up every RETRY_INTERVAL seconds
        and resends any PENDING messages for currently connected clients.
        """
        while self.running:
            time.sleep(RETRY_INTERVAL)
            
            # Use a snapshot of active clients to avoid holding the lock too long
            with self.clients_lock:
                active_snapshot = list(self.active_clients.items())
                
            for sub_id, conn in active_snapshot:
                # Get all messages still marked as PENDING for this subscriber
                pending_msgs = self.queue.get_pending_messages(sub_id)
                
                for msg in pending_msgs:
                    # Increment and check the retry counter
                    retry_count = self.queue.record_retry(msg.msg_id, sub_id)
                    
                    if retry_count > MAX_RETRIES:
                        print(f"[DeliveryManager] Msg {msg.msg_id[-6:]} for {sub_id} exceeded max retries. Marking DEAD_LETTER.")
                        self.queue.mark_dead_letter(msg.msg_id, sub_id)
                    else:
                        print(f"[DeliveryManager] Retrying msg {msg.msg_id[-6:]} for {sub_id} (Attempt {retry_count}/{MAX_RETRIES})")
                        send_message(conn, msg)