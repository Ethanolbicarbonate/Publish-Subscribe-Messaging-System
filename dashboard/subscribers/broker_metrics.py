"""
Subscriber Backend: Broker Metrics
Subscribes to broker system stats and forwards live broker metrics to the dashboard.
"""
import time
from client.subscriber import Subscriber
from common.message import Message

class BrokerMetricsSubscriber:
    def __init__(self, socketio):
        self.socketio = socketio
        self.subscriber = Subscriber(callback=self._on_message, client_id="SUB-METRICS-01")

    def start(self):
        self.subscriber.start()
        time.sleep(1)
        if self.subscriber.connected:
            print("[Broker Metrics] Active. Subscribing to $SYS.BROKER.STATS.")
            self.subscriber.subscribe("$SYS.BROKER.STATS")

    def _on_message(self, msg: Message):
        if msg.payload and isinstance(msg.payload, dict):
            stats_data = {
                "connected_clients": msg.payload.get("connected_clients", 0),
                "connected_clients_list": msg.payload.get("connected_clients_list", []),
                "client_subscriptions": msg.payload.get("client_subscriptions", {}),
                "subscription_patterns": msg.payload.get("subscription_patterns", 0),
                "subscription_patterns_list": msg.payload.get("subscription_patterns_list", []),
                "active_published_topics": msg.payload.get("active_published_topics", 0),
                "active_published_topics_list": msg.payload.get("active_published_topics_list", []),
                "pending_acks": msg.payload.get("pending_acks", 0),
            }
            self.socketio.emit('broker_stats_update', stats_data)

# --- Standalone Tester ---
if __name__ == "__main__":
    class MockSocketIO:
        def emit(self, event, data):
            print(f"[Mock WebSocket Metrics] Emitted '{event}': {data}")

    mock_io = MockSocketIO()
    metrics = BrokerMetricsSubscriber(mock_io)
    metrics.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        metrics.subscriber.stop()
