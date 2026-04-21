"""
Session Manager.
Tracks active connections and handles session resumption.
When a known client reconnects, this manager immediately replays
all PENDING messages from their durable queue.
"""

import threading
import socket
from typing import Dict
from common.protocol import send_message
from broker.queue_manager import QueueManager

class SessionManager:
    def __init__(self, queue_manager: QueueManager, active_clients: Dict[str, socket.socket], clients_lock: threading.Lock):
        self.queue_manager = queue_manager
        self.active_clients = active_clients
        self.clients_lock = clients_lock

    def register_client(self, client_id: str, conn: socket.socket) -> None:
        """
        Registers a connected client into the active pool and immediately 
        triggers a replay of any messages missed while offline.
        """
        with self.clients_lock:
            self.active_clients[client_id] = conn
            
        print(f"[SessionManager] Client {client_id} active. Checking durable queue...")
        self._replay_pending(client_id, conn)

    def deregister_client(self, client_id: str) -> None:
        """Removes a client from the active pool upon disconnection."""
        with self.clients_lock:
            if client_id in self.active_clients:
                del self.active_clients[client_id]

    def _replay_pending(self, client_id: str, conn: socket.socket) -> None:
        """
        Fetches all PENDING messages from the database and sends them 
        immediately over the active socket.
        """
        pending_msgs = self.queue_manager.get_pending_messages(client_id)
        if pending_msgs:
            print(f"[SessionManager] 🔄 Replaying {len(pending_msgs)} missed messages to {client_id}")
            for msg in pending_msgs:
                send_message(conn, msg)