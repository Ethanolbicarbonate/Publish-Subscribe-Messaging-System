"""
Independent Publisher: Crash Simulator
An event-driven script that publishes a massive negative price spike
to trigger downstream alerts, then immediately exits.
"""
import sys
import time
from client.publisher import Publisher

def trigger_crash(target_topic: str, current_price: float, drop_percentage: float):
    pub = Publisher(client_id="PUB-CRASH-SIMULATOR")
    pub.start()
    
    # Wait for connection handshake
    time.sleep(1.0)
    
    if not pub.connected:
        print("[Crash Sim] ❌ Failed to connect to broker.")
        return

    # Calculate the new crashed price
    crashed_price = current_price * (1.0 - (drop_percentage / 100.0))
    symbol = target_topic.split(".")[-1]

    print(f"📉 [Crash Sim] Executing Flash Crash on {symbol}!")
    print(f"   Original: ${current_price:.2f} -> Crashed: ${crashed_price:.2f} (-{drop_percentage}%)")

    payload = {
        "asset_class": "System Event",
        "symbol": symbol,
        "price": round(crashed_price, 2),
        "volume": 9999999, # Massive sell-off volume
        "event": "FLASH_CRASH"
    }

    # Fire the message into the system
    pub.publish(target_topic, payload)
    
    # Sleep briefly to ensure TCP buffer flushes before exiting
    time.sleep(1.0)
    pub.stop()
    print("[Crash Sim] ✅ Payload delivered. Exiting.")

if __name__ == "__main__":
    # Allow passing arguments via command line for testing
    if len(sys.argv) == 4:
        topic = sys.argv[1]
        price = float(sys.argv[2])
        drop = float(sys.argv[3])
    else:
        # Default test fallback
        topic = "MARKET.BLUECHIP.AAPL"
        price = 175.50
        drop = 40.0 # 40% drop

    trigger_crash(topic, price, drop)