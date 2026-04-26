"""
Core Broker TCP Server.
Handles incoming connections, manages a thread pool for clients,
and manages the raw socket lifecycle.
"""
import time
import socket
import threading
import uuid
import concurrent.futures
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
from persistence import db

class Broker:
    """
    Central Publish-Subscribe Broker.
    Listens for TCP connections and delegates message handling to a Thread Pool.
    """
    def __init__(self):
        self.host = HOST
        self.port = BROKER_PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
        
        # --- Thread Pool Optimization ---
        # Limit max concurrent client threads to prevent memory exhaustion
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)
        
        self.topic_manager = TopicManager()
        self.active_clients: Dict[str, socket.socket] = {}
        self.clients_lock = threading.Lock()
        
        self.queue_manager = QueueManager()
        self.delivery_manager = DeliveryManager(self.queue_manager, self.active_clients, self.clients_lock)
        self.session_manager = SessionManager(self.queue_manager, self.active_clients, self.clients_lock)
        self.heartbeat_monitor = HeartbeatMonitor(self.active_clients, self.clients_lock)
        
    def start(self) -> None:
        """Binds the server socket and begins accepting connections in a loop."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = True
        
        self.delivery_manager.start()
        self.heartbeat_monitor.start()
        threading.Thread(target=self._broadcast_stats_loop, daemon=True).start()
        print(f"[Broker] Started successfully. Listening on {self.host}:{self.port}...")
        
        try:
            while self.running:
                conn, addr = self.server_socket.accept()
                print(f"[Broker] 🟢 New connection established from {addr}")
                
                # Submit the client handling task to the Thread Pool
                self.executor.submit(self._handle_client, conn, addr)
                
        except KeyboardInterrupt:
            print("\n[Broker] Shutting down via KeyboardInterrupt...")
        except socket.error as e:
            if self.running:
                print(f"[Broker] Socket error: {e}")
        finally:
            self.stop()
            
    def _handle_client(self, conn: socket.socket, addr: tuple) -> None:
        """
        Dedicated worker function for a single client connection.
        Handles the CONNECT handshake, then reads messages continuously.
        """
        client_id = None
        try:
            init_msg = recv_message(conn)
            if not init_msg or init_msg.type != 'CONNECT':
                print(f"[Broker] ⚠️ Invalid handshake from {addr}. Expected CONNECT. Closing.")
                return
                
            client_id = init_msg.payload.get("client_id")
            if not client_id:
                client_id = str(uuid.uuid4())
                
            welcome_msg = Message(type=TYPE_CONNECTED, payload={"client_id": client_id})
            send_message(conn, welcome_msg)
            
            self.session_manager.register_client(client_id, conn)
            self.heartbeat_monitor.register_client(client_id)

            while self.running:
                msg = recv_message(conn)
                if msg is None:
                    break 
                
                print(f"[Broker] Received [{msg.type}] message from {client_id} ({addr[0]}) on topic '{msg.topic}'")
                
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
            conn.close()

    def _route_message(self, msg: Message) -> None:
        """Finds all matching subscribers for a published message and sends it."""
        matched_subs = self.topic_manager.get_subscribers(msg.topic)
        print(f"[Broker] Routing message {msg.msg_id} to {len(matched_subs)} subscribers.")
        
        for sub_id in matched_subs:
            self.delivery_manager.deliver_message(msg, sub_id)

    def stop(self) -> None:
        """Gracefully shuts down the broker and thread pool."""
        self.running = False
        self.delivery_manager.stop()
        self.heartbeat_monitor.stop()
        
        # Shut down the thread pool, don't wait for threads to finish if forcing exit
        print("[Broker] Shutting down thread pool...")
        self.executor.shutdown(wait=False)
        
        self.server_socket.close()
        print("[Broker] Offline.")
    
    def _broadcast_stats_loop(self):
            """Background thread that publishes broker metrics to a $SYS topic."""
            while self.running:
                time.sleep(2.0)
                
                # Count pending messages from DB directly using the db module
                with db._get_connection() as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM delivery_status WHERE status = ?", ('PENDING',))
                    pending_acks = cursor.fetchone()[0]

                stats_payload = {
                    "connected_clients": len(self.active_clients),
                    "active_topics": len(self.topic_manager._pattern_to_subs),
                    "pending_acks": pending_acks
                }
                
                # Create an internal system message
                sys_msg = Message(
                    type=TYPE_PUBLISH,
                    topic="$SYS.BROKER.STATS",
                    payload=stats_payload
                )
                # Route it just like a normal message
                self._route_message(sys_msg)

if __name__ == "__main__":
    broker = Broker()
    broker.start()