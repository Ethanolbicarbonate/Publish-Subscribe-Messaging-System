"""
Independent Publisher: Blue Chip Stocks
Simulates stable, large-cap market equities with low volatility.
"""
import time
import random
from client.publisher import Publisher

# Baseline data for Blue Chip stocks
BLUE_CHIPS = {
    "AAPL": {"price": 175.50, "baseline": 175.50, "vol": 0.005},
    "MSFT": {"price": 310.20, "baseline": 310.20, "vol": 0.006},
    "JPM":  {"price": 145.80, "baseline": 145.80, "vol": 0.004},
    "V":    {"price": 230.15, "baseline": 230.15, "vol": 0.003}
}

def run_bluechip_feed():
    pub = Publisher(client_id="PUB-BLUECHIP-01")
    pub.start()
    time.sleep(1)
    
    if not pub.connected:
        print("[BlueChip Pub] Failed to connect to broker. Exiting.")
        return

    print("[BlueChip Pub] Feed LIVE. Publishing stable equities...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            for symbol, data in BLUE_CHIPS.items():
                # Random walk based on volatility
                change = random.uniform(-data["vol"], data["vol"])
                data["price"] *= (1 + change)
                
                # Mean reversion (pulls price gently back to baseline)
                difference = data["baseline"] - data["price"]
                data["price"] += (difference * 0.05)
                
                payload = {
                    "asset_class": "Blue Chip",
                    "symbol": symbol,
                    "price": round(data["price"], 2),
                    "volume": random.randint(1000, 10000)
                }
                
                # Publish to a highly specific topic hierarchy
                topic = f"MARKET.BLUECHIP.{symbol}"
                pub.publish(topic, payload)
            
            # Update frequency
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        print("\n[BlueChip Pub] Feed offline.")
    finally:
        pub.stop()

if __name__ == "__main__":
    run_bluechip_feed()