# System Design Decisions

## 1. Topic-Based vs. Content-Based Filtering (Chapter 6.3)
We opted for **Topic-Based Filtering** (e.g., routing based on strings like `MARKET.CRYPTO.BTC` or wildcards like `MARKET.*`).
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
To prevent console spamming, the Alert Subscriber uses **Edge-Triggered Logic**. It tracks the state of each asset and only alerts the user on state *changes* (e.g., when a price drops >5% from its peak, and again when it recovers).

## 5. Real-Time Web Dashboard
The dashboard uses decoupled subscriber backends that connect independently to the broker, forwarding data via WebSockets for live UI updates. This ensures the web interface doesn't interfere with core messaging and allows for granular control (e.g., disconnecting individual subscribers for testing).

## 6. Wildcard Topic Matching
Supports single-level (`*`) and multi-level (`#`) wildcards for flexible subscriptions (e.g., `MARKET.#` catches all market data, while `MARKET.CRYPTO.*` catches only crypto).
