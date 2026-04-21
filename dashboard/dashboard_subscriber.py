"""
Internal Dashboard Subscriber.
Acts as a bridge between the TCP Pub/Sub Broker and the web frontend.
Listens for messages and broadcasts them to browsers via SocketIO.
"""

import time
from client.subscriber import Subscriber
from common.message import Message

class DashboardSubscriber:
    def __init__(self, socketio, broker_stats):
        self.socketio = socketio
        self.stats = broker_stats
        # Use a persistent, easily identifiable client ID for the dashboard
        self.subscriber = Subscriber(callback=self._on_message, client_id="DASHBOARD-PROXY")

    def start(self) -> None:
        """Starts the subscriber and connects to the broker."""
        self.subscriber.start()
        
        # Give it a moment to complete the TCP handshake
        time.sleep(1)
        
        if self.subscriber.connected:
            print("[Dashboard UI] 📡 Dashboard internal subscriber active.")
            self.subscriber.subscribe("STOCK.*")
        else:
            print("[Dashboard UI] ⚠️ Dashboard failed to connect to broker.")

    def _on_message(self, msg: Message) -> None:
        """
        Callback triggered whenever a stock update is received from the broker.
        """
        # 1. Update our local metrics
        self.stats["messages_delivered"] += 1

        # 2. Broadcast the raw message to all connected browsers for charts/logs
        self.socketio.emit('new_message', msg.to_dict())

        # 3. Alert Logic: Check if price thresholds are breached
        price = msg.payload.get("price", 0)
        
        # Hardcoded thresholds for the demo scenario
        if price > 200 or price < 50:
            severity = "critical" if price < 50 else "warning"
            alert_data = {
                "stock": msg.topic.split('.')[-1],  # Extract 'AAPL' from 'STOCK.AAPL'
                "price": price,
                "severity": severity,
                "message": f"Threshold breached: ${price:.2f}",
                "timestamp": msg.timestamp
            }
            # Emit a specific 'alert' event to trigger UI toasts
            self.socketio.emit('alert', alert_data)