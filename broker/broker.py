"""
Core Broker TCP Server.
Handles incoming connections, spins up dedicated client threads,
and manages the raw socket lifecycle.
"""

import socket
import threading
import uuid
from typing import Dict
from common.constants import (
    HOST, BROKER_PORT, TYPE_PUBLISH, TYPE_SUBSCRIBE, 
    TYPE_UNSUBSCRIBE, TYPE_CONNECTED
)
from common.protocol import recv_message, send_message
from common.message import Message
from broker.topic_manager import TopicManager

class Broker:
    """
    Central Publish-Subscribe Broker.
    Listens for TCP connections and delegates message handling to threads.
    """
    def __init__(self):
        self.host = HOST
        self.port = BROKER_PORT
        # Use IPv4 and TCP streams
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow port reuse to avoid "Address already in use" errors during dev restarts
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
        
        # --- Subphase 2.3 Additions ---
        self.topic_manager = TopicManager()
        self.active_clients: Dict[str, socket.socket] = {}
        self.clients_lock = threading.Lock()
        
    def start(self) -> None:
        """Binds the server socket and begins accepting connections in a loop."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = True
        print(f"[Broker] Started successfully. Listening on {self.host}:{self.port}...")
        
        try:
            while self.running:
                # Accept blocks until a new connection arrives
                conn, addr = self.server_socket.accept()
                print(f"[Broker] 🟢 New connection established from {addr}")
                
                # Generate a unique client ID for this session
                client_id = str(uuid.uuid4())
                
                with self.clients_lock:
                    self.active_clients[client_id] = conn
                    
                # Send the client their ID
                welcome_msg = Message(type=TYPE_CONNECTED, payload={"client_id": client_id})
                send_message(conn, welcome_msg)
                
                # Spin up a dedicated thread for this client
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(conn, addr, client_id),
                    daemon=True # Daemons exit when the main thread exits
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\n[Broker] Shutting down via KeyboardInterrupt...")
        except socket.error as e:
            if self.running:
                print(f"[Broker] Socket error: {e}")
        finally:
            self.stop()
            
    def _handle_client(self, conn: socket.socket, addr: tuple, client_id: str) -> None:
        """
        Dedicated thread function for a single client connection.
        Continuously reads messages until the client disconnects.
        """
        try:
            while self.running:
                msg = recv_message(conn)
                if msg is None:
                    # recv_message returns None if the connection is cleanly closed or broken
                    break 
                
                print(f"[Broker] Received [{msg.type}] message from {client_id} ({addr[0]}) on topic '{msg.topic}'")
                
                # --- Subphase 2.3 Routing Logic ---
                if msg.type == TYPE_SUBSCRIBE:
                    self.topic_manager.add_subscription(client_id, msg.topic)
                elif msg.type == TYPE_UNSUBSCRIBE:
                    self.topic_manager.remove_subscription(client_id, msg.topic)
                elif msg.type == TYPE_PUBLISH:
                    self._route_message(msg)
                
        except Exception as e:
            print(f"[Broker] ⚠️ Error handling client {client_id}: {e}")
        finally:
            print(f"[Broker] 🔴 Connection closed for {client_id}")
            with self.clients_lock:
                if client_id in self.active_clients:
                    del self.active_clients[client_id]
            # Clean up all subscriptions associated with the disconnected client
            self.topic_manager.remove_all_subscriptions(client_id)
            conn.close()

    def _route_message(self, msg: Message) -> None:
        """
        Finds all matching subscribers for a published message and sends it to them.
        """
        matched_subs = self.topic_manager.get_subscribers(msg.topic)
        print(f"[Broker] Routing message {msg.msg_id} to {len(matched_subs)} subscribers.")
        
        with self.clients_lock:
            for sub_id in matched_subs:
                if sub_id in self.active_clients:
                    sub_socket = self.active_clients[sub_id]
                    # In Phase 3, we will add persistence and delivery tracking here.
                    # For now, we do a basic best-effort fanout.
                    send_message(sub_socket, msg)

    def stop(self) -> None:
        """Gracefully shuts down the broker."""
        self.running = False
        self.server_socket.close()
        print("[Broker] Offline.")

if __name__ == "__main__":
    broker = Broker()
    broker.start()