import time
from client.subscriber import Subscriber
from common.message import Message
from common.constants import ALERT_HIGH_THRESH, ALERT_LOW_THRESH

class DashboardSubscriber:
    def __init__(self, socketio, broker_stats):
        self.socketio = socketio
        self.stats = broker_stats
        self.subscriber = Subscriber(callback=self._on_message, client_id="DASHBOARD-PROXY")
        self.active_alerts = {}

    def start(self) -> None:
        self.subscriber.start()
        time.sleep(1)
        if self.subscriber.connected:
            print("[Dashboard UI] 📡 Dashboard internal subscriber active.")
            self.subscriber.subscribe("STOCK.*")
            self.subscriber.subscribe("$SYS.BROKER.STATS")

    def _on_message(self, msg: Message) -> None:
        if msg.topic == "$SYS.BROKER.STATS":
            self.stats["connected_clients"] = msg.payload.get("connected_clients", 0)
            self.stats["active_topics"] = msg.payload.get("active_topics", 0)
            self.stats["pending_acks"] = msg.payload.get("pending_acks", 0)
            return 
            
        # 1. Update our local metrics
        self.stats["messages_delivered"] += 1

        # 2. Broadcast the raw message to all connected browsers for charts/logs
        self.socketio.emit('new_message', msg.to_dict())

        # 3. Alert Logic: Edge-Triggered Alerts using Centralized Constants
        price = msg.payload.get("price", 0)
        stock_symbol = msg.topic.split('.')[-1]
        
        in_danger_zone = price > ALERT_HIGH_THRESH or price < ALERT_LOW_THRESH
        already_alerting = self.active_alerts.get(stock_symbol, False)
        
        if in_danger_zone and not already_alerting:
            self.active_alerts[stock_symbol] = True
            severity = "critical" if price < ALERT_LOW_THRESH else "warning"
            alert_data = {
                "stock": stock_symbol,
                "price": price,
                "severity": severity,
                "message": f"Threshold breached: ${price:.2f}",
                "timestamp": msg.timestamp
            }
            self.socketio.emit('alert', alert_data)
            
        elif not in_danger_zone and already_alerting:
            self.active_alerts[stock_symbol] = False
            
            # Emit a RECOVERY alert to the dashboard (Removed emoji)
            alert_data = {
                "stock": stock_symbol,
                "price": price,
                "severity": "success",
                "message": f"Stabilized at ${price:.2f}",
                "timestamp": msg.timestamp
            }
            self.socketio.emit('alert', alert_data)