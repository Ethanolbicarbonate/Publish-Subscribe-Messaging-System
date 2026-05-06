"""
Subscriber Backend: Chart Visualizer
Subscribes to all market data and formats it strictly for UI charts.
"""
import time
from client.subscriber import Subscriber
from common.message import Message

class VisualizerSubscriber:
    def __init__(self, socketio):
        self.socketio = socketio
        # Unique ID for durable queue tracking
        self.subscriber = Subscriber(callback=self._on_message, client_id="SUB-VISUALIZER-01")

    def start(self):
            print("[Visualizer] Active. Subscribing to MARKET.# for charts.")
            self.subscriber.subscribe("MARKET.#")
            self.subscriber.start()

    def _on_message(self, msg: Message):
        price = msg.payload.get("price")
        symbol = msg.payload.get("symbol")
        
        if price is not None and symbol is not None:
            # Format the data cleanly for the frontend charts
            chart_data = {
                "symbol": symbol,
                "price": price,
                "timestamp": msg.timestamp,
                "asset_class": msg.payload.get("asset_class", "Unknown")
            }
            # Broadcast to connected browsers
            self.socketio.emit('chart_update', chart_data)


# Standalone Tester
if __name__ == "__main__":
    class MockSocketIO:
        def emit(self, event, data):
            print(f"[CLI Visualizer] Emitted '{event}': {data['symbol']} @ ${data['price']}")

    print("Testing Visualizer Subscriber independently...")
    mock_io = MockSocketIO()
    vis = VisualizerSubscriber(mock_io)
    vis.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        vis.subscriber.stop()