# System Architecture

## Overview
This system implements a Centralized Broker Publish-Subscribe architecture with a real-time web dashboard.

* **Inter-Process Communication (IPC - Chapter 4):** All components communicate over raw TCP Sockets.
* **Protocol:** To prevent TCP stream fragmentation, we implemented a custom 4-byte length-prefix framing protocol. Every JSON payload is prefixed with its exact byte length so the receiver knows exactly how much data to read.

## Components
1. **The Broker (`broker.py`):**
   * Manages a thread pool for concurrent client connections.
   * `TopicManager`: Handles exact and wildcard (`*`, `#`) subscription matching.
   * `DeliveryManager`: Handles message persistence, queueing, and retry loops.
   * `HeartbeatMonitor`: Aggressively tracks client health and severs dead TCP sockets.
   * Publishes system metrics to `$SYS.BROKER.STATS` topic.

2. **Publishers:**
   * `crypto_publisher.py`: Publishes simulated cryptocurrency prices (BTC, ETH) to `MARKET.CRYPTO.*` topics.
   * `bluechip_publisher.py`: Publishes simulated blue-chip stock prices (AAPL, MSFT) to `MARKET.BLUECHIP.*` topics.
   * `crash_publisher.py`: Publishes crash scenarios for testing alert logic.

3. **Subscribers:**
   * `SUB-VISUALIZER-01`: Dashboard subscriber that visualizes market data on real-time charts.
   * `SUB-ALERTS-01`: Dashboard subscriber that monitors for >5% price drops and emits alerts.
   * `SUB-AUDIT-01`: Dashboard subscriber that logs all messages to a firehose feed.
   * `SUB-METRICS-01`: Dashboard subscriber that displays live broker metrics (connected clients, active topics, pending ACKs).

4. **Dashboard (`dashboard/app.py`):**
   * Web server serving the Subscriber Hub and Publisher Control Center.
   * Uses WebSockets for real-time updates to the UI.
   * Manages independent subscriber backends for decoupled monitoring.

5. **Persistence Layer (`persistence/db.py`):**
   * SQLite database for durable message queues and delivery status.
   * Normalized schema to optimize storage and retrieval.
