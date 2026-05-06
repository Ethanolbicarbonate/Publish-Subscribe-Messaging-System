import time
from client.subscriber import Subscriber
from common.message import Message

class DynamicTesterSubscriber:
    def __init__(self, socketio):
        self.socketio = socketio
        self.subscriber = Subscriber(callback=self._on_message, client_id="SUB-TESTER-01")

    def start(self):
        print("[Dynamic Tester] Active. Awaiting UI commands for subscriptions.")
        self.subscriber.start()

    def _on_message(self, msg: Message):
        log_data = {
            "topic": msg.topic,
            "timestamp": msg.timestamp,
            "payload": msg.payload
        }
        self.socketio.emit('test_log_update', log_data)