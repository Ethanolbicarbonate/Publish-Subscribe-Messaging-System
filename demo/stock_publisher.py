"""
Demo Stock Publisher.
Simulates a live market feed by publishing price updates for multiple stocks
every 2 seconds. Includes a random chance for massive price spikes to 
demonstrate the dashboard's alert system.
"""

import time
import random
from client.publisher import Publisher

# Initial state for our simulated market
STOCKS = {
    "AAPL": {"price": 180.0, "volatility": 0.015},
    "TSLA": {"price": 190.0, "volatility": 0.03},
    "GOOGL": {"price": 135.0, "volatility": 0.02},
    "AMZN": {"price": 145.0, "volatility": 0.025}
}

def run_market():
    # Initialize the publisher with a recognizable ID
    pub = Publisher(client_id="MARKET-FEED-01")
    pub.start()
    
    # Wait a moment for the TCP connection and handshake to complete
    time.sleep(1)
    
    if not pub.connected:
        print("[Demo Publisher] ⚠️ Failed to connect to broker. Exiting.")
        return

    print("📈 Market is OPEN. Publishing live stock feeds...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            for symbol, data in STOCKS.items():
                # 5% chance of a "market shock" to intentionally trigger dashboard alerts
                # (Our dashboard alerts on price > 200 or < 50)
                if random.random() < 0.05:
                    shock = random.uniform(-0.4, 0.5) # -40% to +50% swing
                    data["price"] *= (1 + shock)
                    print(f"⚡ [MARKET SHOCK] Huge swing for {symbol}!")
                else:
                    # Normal random walk based on the stock's volatility
                    change = random.uniform(-data["volatility"], data["volatility"])
                    data["price"] *= (1 + change)
                
                # Prevent negative prices
                data["price"] = max(1.0, data["price"])
                
                # Construct payload
                payload = {
                    "price": round(data["price"], 2),
                    "volume": random.randint(1000, 50000)
                }
                
                # Publish to the specific topic (e.g., STOCK.AAPL)
                pub.publish(f"STOCK.{symbol}", payload)
            
            # Wait 2 seconds before the next batch of updates
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🛑 Market CLOSED (Keyboard Interrupt).")
    finally:
        pub.stop()

if __name__ == "__main__":
    run_market()