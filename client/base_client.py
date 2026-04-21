"""
Base Client.
Provides a resilient TCP socket wrapper with automatic reconnection,
exponential backoff, and background threads for receiving messages
and sending heartbeats.
"""

import socket
import threading
import time
from typing import Optional

from common.constants import HOST, BROKER_PORT, HEARTBEAT_INTERVAL, TYPE_HEARTBEAT
from common.protocol import send_message, recv_message
from common.message import Message

class BaseClient:
    def __init__(self, client_id: Optional[str] = None):
        self.host = HOST
        self.port = BROKER_PORT
        self.client_id = client_id
        self.sock: Optional[socket.socket] = None
        
        self.connected = False
        self.running = False
        self.send_lock = threading.Lock()

    def start(self) -> None:
        """Starts the client and initiates the connection loop."""
        self.running = True
        self.connect()

    def connect(self) -> None:
        """
        Attempts to connect to the broker. If it fails, or if the connection 
        drops later, it retries with exponential backoff.
        """
        backoff = 1.0
        max_backoff = 30.0

        while self.running and not self.connected:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                
                # --- Handshake Phase ---
                init_msg = Message(type='CONNECT', payload={"client_id": self.client_id})
                send_message(self.sock, init_msg)
                
                welcome_msg = recv_message(self.sock)
                if welcome_msg and welcome_msg.type == 'CONNECTED':
                    # If this is our first connection, save the broker-assigned ID
                    if not self.client_id:
                        self.client_id = welcome_msg.payload.get("client_id")
                        
                    self.connected = True
                    print(f"[Client] 🟢 Connected to Broker as {self.client_id}")
                    
                    # Reset backoff on successful connection
                    backoff = 1.0 
                    
                    # Start background daemon threads
                    threading.Thread(target=self._receive_loop, daemon=True).start()
                    threading.Thread(target=self._heartbeat_loop, daemon=True).start()
                    
                    # Hook for subclasses (e.g., to resend subscriptions)
                    self.on_connect()
                    break
                else:
                    print("[Client] ⚠️ Handshake failed. Retrying...")
                    self.sock.close()

            except socket.error:
                print(f"[Client] ⏳ Connection failed. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

    def _receive_loop(self) -> None:
        """Background thread that continuously listens for incoming messages."""
        while self.connected and self.running:
            msg = recv_message(self.sock)
            
            if msg is None:
                print("[Client] 🔴 Connection to broker lost.")
                self.connected = False
                self.sock.close()
                
                # Trigger auto-reconnect if the client wasn't manually stopped
                if self.running:
                    self.connect()
                break
            else:
                self.handle_message(msg)

    def _heartbeat_loop(self) -> None:
        """Background thread that sends periodic pings to keep the session alive."""
        while self.connected and self.running:
            time.sleep(HEARTBEAT_INTERVAL)
            if self.connected:
                hb_msg = Message(type=TYPE_HEARTBEAT)
                self.send(hb_msg)

    def send(self, message: Message) -> bool:
        """Thread-safe method to send a message to the broker."""
        if not self.connected or not self.sock:
            print(f"[Client] Cannot send {message.type}: Not connected.")
            return False
            
        with self.send_lock:
            return send_message(self.sock, message)

    def stop(self) -> None:
        """Gracefully shuts down the client."""
        self.running = False
        self.connected = False
        if self.sock:
            self.sock.close()
        print("[Client] Shut down complete.")

    # --- Hooks for Subclasses ---

    def on_connect(self) -> None:
        """Invoked immediately after a successful connection/reconnection."""
        pass

    def handle_message(self, msg: Message) -> None:
        """Invoked when a message is received. Subclasses must implement this."""
        pass