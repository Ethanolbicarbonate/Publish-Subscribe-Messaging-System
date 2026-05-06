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

from common.constants import HOST, BROKER_PORT, HEARTBEAT_INTERVAL, TYPE_HEARTBEAT, TYPE_CONNECT, TYPE_CONNECTED
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
                
                # Connection Timeout & TCP Keepalive
                self.sock.settimeout(5.0)
                self.sock.connect((self.host, self.port))
                
                self.sock.settimeout(None)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
                init_msg = Message(type=TYPE_CONNECT, payload={"client_id": self.client_id})
                send_message(self.sock, init_msg)
                
                welcome_msg = recv_message(self.sock)
                if welcome_msg and welcome_msg.type == TYPE_CONNECTED:
                    if not self.client_id:
                        self.client_id = welcome_msg.payload.get("client_id")
                        
                    self.connected = True
                    print(f"[Client] Connected to Broker as {self.client_id}")
                    
                    backoff = 1.0 
                    
                    threading.Thread(target=self._receive_loop, daemon=True).start()
                    threading.Thread(target=self._heartbeat_loop, daemon=True).start()
                    
                    self.on_connect()
                    break
                else:
                    print("[Client] Handshake failed. Retrying...")
                    self.sock.close()

            except (socket.error, socket.timeout):
                print(f"[Client] Connection failed. Retrying in {backoff}s...")
                for _ in range(int(backoff * 10)):
                    if not self.running: return
                    time.sleep(0.1)
                backoff = min(backoff * 2, max_backoff)

    def _receive_loop(self) -> None:
        """Background thread that continuously listens for incoming messages."""
        while self.connected and self.running:
            msg = recv_message(self.sock)
            
            if msg is None:
                print("[Client] Connection to broker lost.")
                self.connected = False
                if self.sock:
                    try: self.sock.close()
                    except Exception: pass
                
                if self.running:
                    self.connect()
                break
            else:
                self.handle_message(msg)

    def _heartbeat_loop(self) -> None:
        """Background thread that sends periodic pings to keep the session alive."""
        while self.connected and self.running:
            for _ in range(int(HEARTBEAT_INTERVAL * 10)):
                if not self.connected or not self.running: return
                time.sleep(0.1)
                
            if self.connected:
                hb_msg = Message(type=TYPE_HEARTBEAT)
                success = self.send(hb_msg)
                
                if not success:
                    print(f"[Client] Heartbeat failed. Network dead. Forcing reconnect.")
                    self.connected = False
                    if self.sock:
                        try: self.sock.close()
                        except Exception: pass
                    break

    def send(self, message: Message) -> bool:
        """Thread-safe method to send a message to the broker."""
        if not self.connected or not self.sock:
            return False
            
        with self.send_lock:
            return send_message(self.sock, message)

    def stop(self) -> None:
        """Gracefully shuts down the client."""
        self.running = False
        self.connected = False
        if self.sock:
            try: self.sock.close()
            except Exception: pass
        print("[Client] Shut down complete.")

    def on_connect(self) -> None:
        pass

    def handle_message(self, msg: Message) -> None:
        pass