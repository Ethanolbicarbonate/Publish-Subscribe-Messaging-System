"""
Subscriber Backend: Audit Log
Subscribes to ALL topics (#) and captures the raw message data.
Represents an unadulterated "firehose" stream for compliance/logging.
"""
import time
import json
from client.subscriber import Subscriber
from common.message import Message

class AuditLogSubscriber:
    def __init__(self, socketio):
        self.socketio = socketio
        self.subscriber = Subscriber(callback=self._on_message, client_id="SUB-AUDIT-01")

    def start(self):
            print("[Audit Log] Active. Subscribing to # (Firehose).")
            self.subscriber.subscribe("#")
            self.subscriber.start()

    def _on_message(self, msg: Message):
        # exact raw dictionary representation
        raw_data = msg.to_dict()
        
        # Broadcast the raw data to the frontend log panel
        self.socketio.emit('audit_update', raw_data)

# --- Standalone Tester ---
if __name__ == "__main__":
    class MockSocketIO:
        def emit(self, event, data):
            # truncated version of the raw JSON so it fits on one line
            raw_json = json.dumps(data)
            print(f"[Mock WebSocket Firehose] {raw_json[:100]}...")

    print("Testing Audit Log Subscriber independently...")
    mock_io = MockSocketIO()
    audit = AuditLogSubscriber(mock_io)
    audit.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        audit.subscriber.stop()