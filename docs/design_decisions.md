# System Design Decisions

## 1. Topic-Based vs. Content-Based Filtering (Chapter 6.3)
We opted for **Topic-Based Filtering** (e.g., routing based on strings like `STOCK.AAPL` or wildcards like `STOCK.*`). 
* **Why not Content-Based?** Content-based filtering requires the broker to deserialize and inspect every JSON payload to evaluate rules (e.g., `price > 200`). This is highly CPU-intensive. By using Topic-based filtering, the broker acts purely as a fast router, remaining agnostic to the payload data and allowing for much higher system throughput.

## 2. At-Least-Once Delivery & Durable Queues
To handle subscriber disconnections, the system guarantees **At-Least-Once Delivery**. 
* When a message is published, it is immediately written to a **Durable Queue** (SQLite Database) with a `PENDING` status. 
* If a client abruptly disconnects, the messages queue up safely on disk.
* Upon reconnection, the `SessionManager` immediately replays all missed messages.

## 3. Database Normalization for Persistence
Saving heavy JSON payloads for multiple subscribers wastes disk I/O. We implemented a **Normalized Database Schema**:
1. `messages` table: Stores the heavy payload exactly once.
2. `delivery_status` table: A lightweight junction table that tracks the `PENDING/DELIVERED` state for each specific subscriber.

## 4. Edge-Triggered Alerting
To prevent console spamming, the Alert Subscriber uses **Edge-Triggered Logic**. It tracks the state of each stock and only alerts the user on state *changes* (e.g., when a price crosses above $200, and again when it recovers).