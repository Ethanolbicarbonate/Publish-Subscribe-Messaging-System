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
    
    time.sleep(1.0)
    
    if not pub.connected:
        print("[Crash Sim] Failed to connect to broker.")
        return

    crashed_price = current_price * (1.0 - (drop_percentage / 100.0))
    symbol = target_topic.split(".")[-1]

    print(f"[Crash Sim] Executing Flash Crash on {symbol}!")
    print(f"Original: ${current_price:.2f} -> Crashed: ${crashed_price:.2f} (-{drop_percentage}%)")

    payload = {
        "asset_class": "System Event",
        "symbol": symbol,
        "price": round(crashed_price, 2),
        "volume": 9999999,
        "event": "FLASH_CRASH"
    }

    pub.publish(target_topic, payload)
    
    time.sleep(1.0)
    pub.stop()
    print("[Crash Sim] Payload delivered. Exiting.")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        topic = sys.argv[1]
        price = float(sys.argv[2])
        drop = float(sys.argv[3])
    else:
        topic = "MARKET.BLUECHIP.AAPL"
        price = 175.50
        drop = 40.0 #%

    trigger_crash(topic, price, drop)