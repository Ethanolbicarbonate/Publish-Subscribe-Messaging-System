"""
Crash Simulation & Recovery Test.
Demonstrates the broker's fault tolerance by killing a subscriber mid-stream
and verifying message queuing and replay upon reconnection.
"""

import time
import multiprocessing
import os
from client.publisher import Publisher
from client.subscriber import Subscriber
from common.message import Message

def run_publisher():
    """Runs a publisher that sends 10 messages, one every second."""
    pub = Publisher()
    pub.start()
    time.sleep(1) # Wait for connection
    
    for i in range(1, 11):
        pub.publish("STOCK.AAPL", {"price": 100 + i, "seq": i})
        print(f"[Pub] 📤 Sent message {i}/10")
        time.sleep(1)
        
    pub.stop()

def run_failing_subscriber():
    """Runs a subscriber that crashes abruptly after 3 seconds."""
    def on_msg(msg: Message):
        print(f"[Sub 1] 📥 Received: {msg.payload}")
        
    sub = Subscriber(callback=on_msg, client_id="CRASH-TEST-SUB")
    sub.start()
    time.sleep(0.5)
    sub.subscribe("STOCK.AAPL")
    
    time.sleep(3)
    print("\n[Sub 1] 💥 SIMULATING FATAL CRASH! (Process abruptly killed)")
    # Force kill the process without closing sockets or sending disconnects
    os._exit(1) 

def run_recovery_subscriber():
    """Reconnects the subscriber to receive queued messages."""
    def on_msg(msg: Message):
        print(f"[Sub 2 (Recovery)] 📥 Received Queued/Replayed Msg: {msg.payload}")
        
    print("\n[Sub 2] 🔄 Reconnecting to Broker to recover missed messages...")
    sub = Subscriber(callback=on_msg, client_id="CRASH-TEST-SUB")
    sub.start()
    
    # Wait to allow messages to stream in
    time.sleep(4)
    sub.stop()

if __name__ == "__main__":
    print("=== Starting Crash Simulation ===")
    print("Ensure the Broker is currently running in another terminal window!\n")
    
    # 1. Start Publisher in a separate process
    pub_process = multiprocessing.Process(target=run_publisher)
    pub_process.start()
    
    # 2. Start the subscriber that will crash
    fail_process = multiprocessing.Process(target=run_failing_subscriber)
    fail_process.start()
    
    # Wait for the first subscriber to crash
    fail_process.join() 
    
    # 3. Wait a few seconds to let the publisher queue up messages on the broker
    print("\n[System] Waiting 4 seconds. The broker is queueing these messages...")
    time.sleep(4)
    
    # 4. Spin up the recovery subscriber
    run_recovery_subscriber()
    
    # Wait for the publisher to finish
    pub_process.join()
    print("\n=== Crash Simulation Complete ===")