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
    TYPE_UNSUBSCRIBE, TYPE_CONNECTED, TYPE_ACK, TYPE_HEARTBEAT
)
from common.protocol import recv_message, send_message
from common.message import Message
from broker.topic_manager import TopicManager
from broker.queue_manager import QueueManager
from broker.delivery_manager import DeliveryManager
from broker.session_manager import SessionManager
from broker.heartbeat_monitor import HeartbeatMonitor

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
        
        # --- Subphase 3.2 Additions ---
        self.queue_manager = QueueManager()
        self.delivery_manager = DeliveryManager(self.queue_manager, self.active_clients, self.clients_lock)
        
        # --- Subphase 3.3 Additions ---
        self.session_manager = SessionManager(self.queue_manager, self.active_clients, self.clients_lock)
        
        # --- Subphase 5.1 Additions ---
        self.heartbeat_monitor = HeartbeatMonitor(self.active_clients, self.clients_lock)
        
    def start(self) -> None:
        """Binds the server socket and begins accepting connections in a loop."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = True
        
        self.delivery_manager.start()
        self.heartbeat_monitor.start()
        print(f"[Broker] Started successfully. Listening on {self.host}:{self.port}...")
        
        try:
            while self.running:
                # Accept blocks until a new connection arrives
                conn, addr = self.server_socket.accept()
                print(f"[Broker] 🟢 New connection established from {addr}")
                
                # --- Subphase 3.3 Change: Handshake moved to client thread ---
                # Spin up a dedicated thread for this client
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(conn, addr),
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
            
    def _handle_client(self, conn: socket.socket, addr: tuple) -> None:
        """
        Dedicated thread function for a single client connection.
        Handles the CONNECT handshake, then reads messages continuously.
        """
        client_id = None
        try:
            # --- Handshake Phase ---
            init_msg = recv_message(conn)
            if not init_msg or init_msg.type != 'CONNECT':
                print(f"[Broker] ⚠️ Invalid handshake from {addr}. Expected CONNECT. Closing.")
                return
                
            client_id = init_msg.payload.get("client_id")
            if not client_id:
                # New client, generate a UUID
                client_id = str(uuid.uuid4())
                
            # Send the client their ID
            welcome_msg = Message(type=TYPE_CONNECTED, payload={"client_id": client_id})
            send_message(conn, welcome_msg)
            
            # Register the session (Triggers durable queue replay)
            self.session_manager.register_client(client_id, conn)
            self.heartbeat_monitor.register_client(client_id)

            # --- Message Loop Phase ---
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
                elif msg.type == TYPE_ACK:
                    msg_id = msg.payload.get("msg_id")
                    if msg_id:
                        self.delivery_manager.handle_ack(msg_id, client_id)
                elif msg.type == TYPE_HEARTBEAT:
                    self.heartbeat_monitor.record_heartbeat(client_id)
                
        except Exception as e:
            print(f"[Broker] ⚠️ Error handling client {client_id}: {e}")
        finally:
            if client_id:
                print(f"[Broker] 🔴 Connection closed for {client_id}")
                self.session_manager.deregister_client(client_id)
                self.heartbeat_monitor.remove_client(client_id)
                # CRITICAL: We NO LONGER remove subscriptions on disconnect! 
                # If we did, the durable queue wouldn't capture messages while the client is offline.
            conn.close()

    def _route_message(self, msg: Message) -> None:
        """
        Finds all matching subscribers for a published message and sends it to them.
        """
        matched_subs = self.topic_manager.get_subscribers(msg.topic)
        print(f"[Broker] Routing message {msg.msg_id} to {len(matched_subs)} subscribers.")
        
        for sub_id in matched_subs:
            # Delegate to delivery manager for persistence and sending
            self.delivery_manager.deliver_message(msg, sub_id)

    def stop(self) -> None:
        """Gracefully shuts down the broker."""
        self.running = False
        self.delivery_manager.stop()
        self.heartbeat_monitor.stop()
        self.server_socket.close()
        print("[Broker] Offline.")

if __name__ == "__main__":
    broker = Broker()
    broker.start()