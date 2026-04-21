"""
Core Broker TCP Server.
Handles incoming connections, spins up dedicated client threads,
and manages the raw socket lifecycle.
"""

import socket
import threading
from common.constants import HOST, BROKER_PORT
from common.protocol import recv_message

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
        Continuously reads messages until the client disconnects.
        """
        try:
            while self.running:
                msg = recv_message(conn)
                if msg is None:
                    # recv_message returns None if the connection is cleanly closed or broken
                    break 
                
                print(f"[Broker] Received [{msg.type}] message from {addr} on topic '{msg.topic}'")
                
                # Note: In Subphase 2.2 and 2.3, we will pass this message to the TopicManager
                
        except Exception as e:
            print(f"[Broker] ⚠️ Error handling client {addr}: {e}")
        finally:
            print(f"[Broker] 🔴 Connection closed from {addr}")
            conn.close()

    def stop(self) -> None:
        """Gracefully shuts down the broker."""
        self.running = False
        self.server_socket.close()
        print("[Broker] Offline.")

if __name__ == "__main__":
    broker = Broker()
    broker.start()