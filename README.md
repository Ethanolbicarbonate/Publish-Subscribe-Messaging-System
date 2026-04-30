# Pub/Sub Distributed Messaging System

A Python-based Publish-Subscribe middleware system featuring persistent queues, at-least-once delivery, and topic-based filtering.

## Project Deliverables
- `docs/architecture.md` — system architecture overview
- `docs/design_decisions.md` — design rationale and trade-offs
- `docs/diagrams/` — architecture and workflow diagrams
- `docs/System_Diagram_Document.pdf` — final document of the whole project
- `tests/` — validation and simulation tests
- `demo/` — demo publisher/subscriber scripts 

## How to Run the Demo
1. Open 4 terminals and run:
    - In Terminal 1, type: python -m broker.broker
    - In Terminal 2, type: python -m dashboard.app
    - In Terminal 3, type: python -m demo.stock_publisher
    - In Terminal 4, type: python -m demo.alert_subscriber
2. Open your web browser and navigate to: http://localhost:8080
3. To test fault tolerance (Durable Queues), forcefully kill the CLI Subscriber in the terminal (Ctrl+C), wait for the Pending ACKs to rise on the dashboard, and then restart the subscriber to watch the queue replay.
