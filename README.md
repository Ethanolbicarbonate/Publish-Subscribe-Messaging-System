# Pub/Sub Distributed Messaging System
Repo link: https://github.com/Ethanolbicarbonate/Publish-Subscribe-Messaging-System

A Python-based Publish-Subscribe middleware system featuring persistent queues, at-least-once delivery, topic-based filtering, and a real-time web dashboard.

## Project Deliverables
- `docs/architecture.md` — system architecture overview
- `docs/design_decisions.md` — design rationale and trade-offs
- `docs/diagrams/` — architecture and workflow diagrams
- `docs/System_Design_Document.pdf` — final document of the whole project
- `demo/` — demo publisher scripts

## Publishers
- `crypto_publisher.py` — Publishes simulated cryptocurrency prices (BTC, ETH, SOL, DOGE) with random walks and volatility.
- `bluechip_publisher.py` — Publishes simulated blue-chip stock prices (AAPL, MSFT, JPM, V) with mean reversion.
- `crash_publisher.py` — Publishes crash scenarios for testing alert logic.

## Subscribers
- `SUB-VISUALIZER-01` — Dashboard subscriber that visualizes market data on charts.
- `SUB-ALERTS-01` — Dashboard subscriber that monitors for >5% price drops and alerts.
- `SUB-AUDIT-01` — Dashboard subscriber that logs all messages to a firehose feed.
- `SUB-METRICS-01` — Dashboard subscriber that displays live broker metrics.

## Topics
The system uses hierarchical topic names with dot-separated levels. Publishers send messages to specific concrete topics, while subscribers can use wildcards (`*` for single level, `#` for multi-level) to match multiple topics.

**Published Topics:**
- `MARKET.CRYPTO.BTC` — Simulated Bitcoin price data (price, timestamp).
- `MARKET.CRYPTO.ETH` — Simulated Ethereum price data (price, timestamp).
- `MARKET.CRYPTO.SOL` — Simulated Solana price data (price, timestamp).
- `MARKET.CRYPTO.DOGE` — Simulated Dogecoin price data (price, timestamp).
- `MARKET.BLUECHIP.AAPL` — Simulated Apple stock price data (price, timestamp).
- `MARKET.BLUECHIP.MSFT` — Simulated Microsoft stock price data (price, timestamp).
- `MARKET.BLUECHIP.JPM` — Simulated JPMorgan stock price data (price, timestamp).
- `MARKET.BLUECHIP.V` — Simulated Visa stock price data (price, timestamp).
- `$SYS.BROKER.STATS` — Live broker metrics (connected clients, active topics, pending ACKs).

**Subscription Patterns Used:**
- `MARKET.#` — Matches all market data topics (used by visualizer and alerts subscribers).
- `#` — Matches all topics (used by audit subscriber).
- `$SYS.BROKER.STATS` — Matches broker stats (used by metrics subscriber).

## How to Run the Demo
1. Open multiple terminals and run:
    - Terminal 1: `python -m broker.broker` (starts the broker server)
    - Terminal 2: `python -m dashboard.app` (starts the web dashboard)
    - Terminal 3: `python -m publisher.crypto_publisher` (starts crypto price publisher)
    - Terminal 4: `python -m publisher.bluechip_publisher` (starts stock price publisher)
    - Optional: `python -m publisher.crash_publisher MARKET.CRYPTO.BTC 60000 30` (triggers a crash scenario)
2. Open your web browser and navigate to: http://localhost:8080/subscribers
3. To test fault tolerance (Durable Queues), disconnect a subscriber from the dashboard (e.g., SUB-VISUALIZER-01), wait for Pending ACKs to rise, then reconnect to watch the queue replay.

---

Aquino, Dallas A. <br>
Buñag, Frederick Jibril L. <br>
Carbonell, Ethan Jed V. <br>
Corpes, Vincent L. Jr. <br>

BSCS 3A AI

