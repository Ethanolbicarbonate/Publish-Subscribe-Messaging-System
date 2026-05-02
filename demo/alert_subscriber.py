import time
from client.subscriber import Subscriber
from common.message import Message

ALERT_HIGH_THRESH = 200.0
ALERT_LOW_THRESH = 50.0

# ANSI Color Codes for terminal output
COLOR_RED = '\033[91m'
COLOR_AMBER = '\033[93m'
COLOR_GREEN = '\033[92m'
COLOR_RESET = '\033[0m'

def create_callback():
    # Dictionary to track state for Edge-Triggered logic
    active_alerts = {}
    
    def on_message(msg: Message):
        try:
            price = msg.payload.get("price")
            if price is None:
                return
                
            stock_symbol = msg.topic.split('.')[-1]
            
            # log for EVERY message so we can visually see the Queue Replay
            print(f"  [Trace] {stock_symbol} updated to ${price:.2f}")
            
            # Check thresholds using the central constants
            in_danger = price > ALERT_HIGH_THRESH or price < ALERT_LOW_THRESH
            is_alerting = active_alerts.get(stock_symbol, False)
            
            if in_danger and not is_alerting:
                # STATE CHANGE: Normal -> Danger
                active_alerts[stock_symbol] = True
                
                if price > ALERT_HIGH_THRESH:
                    print(f"{COLOR_AMBER}[WARNING] {stock_symbol} surged to ${price:.2f} (>{ALERT_HIGH_THRESH}){COLOR_RESET}")
                elif price < ALERT_LOW_THRESH:
                    print(f"{COLOR_RED}[CRITICAL] {stock_symbol} plummeted to ${price:.2f} (<{ALERT_LOW_THRESH}){COLOR_RESET}")
                    
            elif not in_danger and is_alerting:
                # STATE CHANGE: Danger -> Normal
                active_alerts[stock_symbol] = False
                print(f"{COLOR_GREEN}[RECOVERED] {stock_symbol} stabilized at ${price:.2f}{COLOR_RESET}")
                
        except Exception as e:
            print(f"Error processing message: {e}")
            
    return on_message

def run_alert_system():
    print(f"Starting CLI Alert System (Edge-Triggered).")
    print(f"   Monitoring for prices > ${ALERT_HIGH_THRESH} or < ${ALERT_LOW_THRESH}...")
    
    callback = create_callback()
    sub = Subscriber(callback=callback, client_id="CLI-ALERT-SYSTEM-01")
    
    sub.start()
    time.sleep(1)
    
    if sub.connected:
        print("Connected to Broker. Subscribing to STOCK.*")
        sub.subscribe("STOCK.*")
    else:
        print("Failed to connect to broker.")
        return
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Alert System...")
        sub.stop()
    
if __name__ == "__main__":
    run_alert_system()