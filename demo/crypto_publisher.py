"""
Independent Publisher: Cryptocurrency Feed
Simulates highly volatile digital assets.
"""
import time
import random
from client.publisher import Publisher

# Baseline data for Crypto assets (higher volatility than blue chips)
CRYPTO = {
    "BTC":  {"price": 62000.00, "baseline": 62000.00, "vol": 0.03},
    "ETH":  {"price": 3400.00,  "baseline": 3400.00,  "vol": 0.04},
    "SOL":  {"price": 145.00,   "baseline": 145.00,   "vol": 0.06},
    "DOGE": {"price": 0.15,     "baseline": 0.15,     "vol": 0.08}
}

def run_crypto_feed():
    pub = Publisher(client_id="PUB-CRYPTO-01")
    pub.start()
    time.sleep(1)
    
    if not pub.connected:
        print("[Crypto Pub] Failed to connect to broker. Exiting.")
        return

    print("[Crypto Pub] Feed LIVE. Publishing volatile digital assets...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            for symbol, data in CRYPTO.items():
                # Occasional large swings (10% chance)
                if random.random() < 0.10:
                    swing = random.uniform(-0.15, 0.15) # Up to 15% instant swing
                    data["price"] *= (1 + swing)
                    print(f"   [Crypto Pub] Volatility spike on {symbol}!")
                else:
                    # Normal random walk
                    change = random.uniform(-data["vol"], data["vol"])
                    data["price"] *= (1 + change)
                
                # Weak mean reversion for crypto
                difference = data["baseline"] - data["price"]
                data["price"] += (difference * 0.02)
                
                payload = {
                    "asset_class": "Crypto",
                    "symbol": symbol,
                    "price": round(data["price"], 4 if symbol == "DOGE" else 2),
                    "volume": random.randint(50000, 1000000)
                }
                
                # Publish to the Crypto topic hierarchy
                topic = f"MARKET.CRYPTO.{symbol}"
                pub.publish(topic, payload)
            
            # Crypto markets move faster!
            time.sleep(0.8)
            
    except KeyboardInterrupt:
        print("\n[Crypto Pub] Feed offline.")
    finally:
        pub.stop()

if __name__ == "__main__":
    run_crypto_feed()