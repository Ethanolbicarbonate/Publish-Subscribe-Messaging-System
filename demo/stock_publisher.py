import time
import random
from client.publisher import Publisher

# Added "baseline" to simulate market gravity (Mean Reversion)
STOCKS = {
    "AAPL": {"price": 180.0, "baseline": 180.0, "volatility": 0.015},
    "TSLA": {"price": 190.0, "baseline": 190.0, "volatility": 0.03},
    "GOOGL": {"price": 135.0, "baseline": 135.0, "volatility": 0.02},
    "AMZN": {"price": 145.0, "baseline": 145.0, "volatility": 0.025}
}

def run_market():
    pub = Publisher(client_id="MARKET-FEED-01")
    pub.start()
    time.sleep(1)
    
    if not pub.connected:
        print("[Demo Publisher] ⚠️ Failed to connect to broker. Exiting.")
        return

    print("📈 Market is OPEN. Publishing live stock feeds (with Mean Reversion)...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            for symbol, data in STOCKS.items():
                
                # 1. Market Shocks (5% chance to cause an alert)
                if random.random() < 0.05:
                    shock = random.uniform(-0.4, 0.5) # -40% to +50% swing
                    data["price"] *= (1 + shock)
                    print(f"⚡ [MARKET SHOCK] Huge swing for {symbol}!")
                else:
                    # 2. Normal random walk
                    change = random.uniform(-data["volatility"], data["volatility"])
                    data["price"] *= (1 + change)
                
                # 3. GRAVITY (Mean Reversion)
                # Pulls the stock back toward its baseline by 10% every tick
                # This ensures stocks don't drift above 200 forever!
                difference = data["baseline"] - data["price"]
                data["price"] += (difference * 0.10)
                
                # Prevent negative prices
                data["price"] = max(1.0, data["price"])
                
                # Construct payload
                payload = {
                    "price": round(data["price"], 2),
                    "volume": random.randint(1000, 50000)
                }
                
                pub.publish(f"STOCK.{symbol}", payload)
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Market CLOSED.")
    finally:
        pub.stop()

if __name__ == "__main__":
    run_market()