# System Architecture

## Overview
This system implements a Centralized Broker Publish-Subscribe architecture.

* **Inter-Process Communication (IPC - Chapter 4):** All components communicate over raw TCP Sockets.
* **Protocol:** To prevent TCP stream fragmentation, we implemented a custom 4-byte length-prefix framing protocol. Every JSON payload is prefixed with its exact byte length so the receiver knows exactly how much data to read.

## Components
1. **The Broker (`broker.py`):** 
   * Manages a thread pool for concurrent client connections.
   * `TopicManager`: Handles exact and wildcard (`*`) subscription matching.
   * `DeliveryManager`: Handles message persistence, queueing, and retry loops.
   * `HeartbeatMonitor`: Aggressively tracks client health and severs dead TCP sockets.
2. **Publishers (`stock_publisher.py`):**
   * Pushes simulated market data to specific topics. Implements "Mean Reversion" (gravity) and market shocks.
3. **Subscribers (`alert_subscriber.py` & `dashboard_subscriber.py`):**
   * Listens to topics. When a message is received and processed, they return an `ACK` to the broker to fulfill the At-Least-Once delivery guarantee.