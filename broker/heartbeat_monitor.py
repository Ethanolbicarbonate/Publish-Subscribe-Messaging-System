"""
Heartbeat Monitor.
Tracks client heartbeats and aggressively closes connections 
for clients that stop responding, ensuring accurate OFFLINE status.
"""

import threading
import time
import socket
from typing import Dict
from common.constants import HEARTBEAT_INTERVAL, MISSED_HEARTBEATS_LIMIT

class HeartbeatMonitor:
    def __init__(self, active_clients: Dict[str, socket.socket], clients_lock: threading.Lock):
        self.active_clients = active_clients
        self.clients_lock = clients_lock
        
        self.last_heartbeats: Dict[str, float] = {}
        self._hb_lock = threading.Lock()
        
        self.running = False
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)

    def start(self) -> None:
        """Starts the background tracking thread."""
        self.running = True
        self.monitor_thread.start()
        print("[HeartbeatMonitor] Background tracking thread started.")

    def stop(self) -> None:
        """Stops the tracking thread."""
        self.running = False

    def register_client(self, client_id: str) -> None:
        """Initializes the heartbeat timer for a newly connected client."""
        with self._hb_lock:
            self.last_heartbeats[client_id] = time.time()

    def record_heartbeat(self, client_id: str) -> None:
        """Updates the last seen timestamp for a client."""
        with self._hb_lock:
            self.last_heartbeats[client_id] = time.time()

    def remove_client(self, client_id: str) -> None:
        """Cleans up tracking data when a client cleanly disconnects."""
        with self._hb_lock:
            self.last_heartbeats.pop(client_id, None)

    def _monitor_loop(self) -> None:
        """
        Background loop that periodically checks for dead clients.
        Closes the socket if they miss the configured limit of heartbeats.
        """
        check_interval = 5.0
        timeout_threshold = HEARTBEAT_INTERVAL * MISSED_HEARTBEATS_LIMIT

        while self.running:
            time.sleep(check_interval)
            now = time.time()
            
            with self.clients_lock:
                client_ids = list(self.active_clients.keys())
                
            for client_id in client_ids:
                with self._hb_lock:
                    last_hb = self.last_heartbeats.get(client_id)
                
                if last_hb is not None and (now - last_hb) > timeout_threshold:
                    print(f"[HeartbeatMonitor] Client {client_id} timed out (Missed heartbeats). Marking OFFLINE.")
                    
                    # Close the socket to force a clean disconnect in the worker thread
                    with self.clients_lock:
                        conn = self.active_clients.get(client_id)
                        if conn:
                            try:
                                conn.close()
                            except Exception:
                                pass
                    
                    self.remove_client(client_id)