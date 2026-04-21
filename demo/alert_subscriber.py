"""
Demo Alert Subscriber.
A CLI-based subscriber that listens to all stock topics and prints
colored alerts to the terminal when prices breach configured thresholds.
"""

import time
from client.subscriber import Subscriber
from common.message import Message

# Alert Thresholds
HIGH_THRESHOLD = 200.0
LOW_THRESHOLD = 50.0

# ANSI Color Codes for terminal output
COLOR_RED = '\033[91m'
COLOR_AMBER = '\033[93m'
COLOR_RESET = '\033[0m'

def on_message(msg: Message):
    """Callback triggered on every received message."""
    try:
        price = msg.payload.get("price")
        if price is None:
            return
            
        stock_symbol = msg.topic.split('.')[-1]
        
        # Check thresholds and print colored alerts
        if price > HIGH_THRESHOLD:
            print(f"{COLOR_AMBER}🚨 [WARNING] {stock_symbol} surged above ${HIGH_THRESHOLD:.2f}! Current: ${price:.2f}{COLOR_RESET}")
        elif price < LOW_THRESHOLD:
            print(f"{COLOR_RED}💥 [CRITICAL] {stock_symbol} plummeted below ${LOW_THRESHOLD:.2f}! Current: ${price:.2f}{COLOR_RESET}")
            
    except Exception as e:
        print(f"Error processing message: {e}")

def run_alert_system():
    """Initializes the subscriber and starts listening for market data."""
    print(f"🛡️ Starting CLI Alert System.")
    print(f"Monitoring for prices > ${HIGH_THRESHOLD} or < ${LOW_THRESHOLD}...")
    
    # Initialize subscriber with a fixed ID so it can recover missed alerts if it crashes
    sub = Subscriber(callback=on_message, client_id="CLI-ALERT-SYSTEM-01")
    sub.start()
    
    time.sleep(1) # Wait for network handshake
    
    if sub.connected:
        sub.subscribe("STOCK.*")
        print("✅ Subscribed to 'STOCK.*'. Listening for market shocks...\n")
    else:
        print("⚠️ Failed to connect to broker. Exiting.")
        return

    try:
        # Keep the main thread alive while the background thread receives messages
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Alert System.")
    finally:
        sub.stop()

if __name__ == "__main__":
    run_alert_system()