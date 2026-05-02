"""
Subscriber Backend: Alert Monitor
Subscribes to all market data and tracks high-water marks.
Emits alerts only when an asset drops > 5% from its peak.
"""
import time
from client.subscriber import Subscriber
from common.message import Message

class AlertMonitorSubscriber:
    def __init__(self, socketio):
        self.socketio = socketio
        self.subscriber = Subscriber(callback=self._on_message, client_id="SUB-ALERTS-01")
        
        # State tracking for dynamic thresholds
        self.high_water_marks = {}
        self.active_alerts = {}

    def start(self):
        self.subscriber.start()
        time.sleep(1)
        if self.subscriber.connected:
            print("[Alert Monitor] Active. Subscribing to MARKET.# for anomaly detection.")
            self.subscriber.subscribe("MARKET.#")

    def _on_message(self, msg: Message):
        price = msg.payload.get("price")
        symbol = msg.payload.get("symbol")
        
        if price is None or symbol is None:
            return

        # 1. Update the High-Water Mark (Peak Price)
        if symbol not in self.high_water_marks:
            self.high_water_marks[symbol] = price
        else:
            self.high_water_marks[symbol] = max(self.high_water_marks[symbol], price)

        peak = self.high_water_marks[symbol]
        
        # 2. Calculate percentage drop from peak
        drop_pct = ((peak - price) / peak) * 100.0

        # 3. Edge-Triggered Alert Logic (> 5% drop)
        is_crashing = drop_pct >= 5.0
        currently_alerting = self.active_alerts.get(symbol, False)

        if is_crashing and not currently_alerting:
            # STATE CHANGE: Normal -> Crash
            self.active_alerts[symbol] = True
            alert_data = {
                "symbol": symbol,
                "price": price,
                "severity": "critical",
                "message": f"CRASH: {symbol} down {drop_pct:.1f}% from peak! (${price:.2f})",
                "timestamp": msg.timestamp
            }
            self.socketio.emit('alert_update', alert_data)
            
        elif not is_crashing and currently_alerting:
            # STATE CHANGE: Crash -> Recovered
            self.active_alerts[symbol] = False
            alert_data = {
                "symbol": symbol,
                "price": price,
                "severity": "success",
                "message": f"RECOVERY: {symbol} stabilized at ${price:.2f}.",
                "timestamp": msg.timestamp
            }
            self.socketio.emit('alert_update', alert_data)

# --- Standalone Tester ---
if __name__ == "__main__":
    class MockSocketIO:
        def emit(self, event, data):
            # emojis based on severity for terminal debugging
            icon = "🔴" if data["severity"] == "critical" else "🟢"
            print(f"\n{icon} [Mock WebSocket Alert] {data['message']}")

    print("Testing Alert Monitor Subscriber independently...")
    mock_io = MockSocketIO()
    monitor = AlertMonitorSubscriber(mock_io)
    monitor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.subscriber.stop()