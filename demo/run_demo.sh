#!/bin/bash
# Demo Launcher for the Pub/Sub System.
# Launches all components and optionally runs a fault-tolerance crash test.

echo "=== 🚀 Starting Pub/Sub Distributed System ==="

# 1. Start the Broker Core
echo "[1/4] Starting Broker..."
python -m broker.broker &
BROKER_PID=$!
sleep 2 # Give the broker time to bind to the port

# 2. Start the Web Dashboard
echo "[2/4] Starting Web Dashboard..."
python -m dashboard.app &
DASHBOARD_PID=$!
sleep 2

# 3. Start the Live Stock Publisher
echo "[3/4] Starting Stock Market Feed..."
python -m demo.stock_publisher &
PUB_PID=$!
sleep 1

# 4. Start the CLI Alert Subscriber
echo "[4/4] Starting CLI Alert Subscriber..."
python -m demo.alert_subscriber &
SUB_PID=$!

# Define a cleanup function to gracefully shut down all background processes on exit
cleanup() {
    echo -e "\n🛑 Shutting down all system components..."
    kill $BROKER_PID $DASHBOARD_PID $PUB_PID $SUB_PID 2>/dev/null
    echo "System offline."
    exit
}
# Trap Ctrl+C (SIGINT) to run the cleanup function
trap cleanup SIGINT SIGTERM

echo "✅ System is fully operational!"
echo "🌐 Open your browser to http://localhost:8080 to view the live dashboard."

# --- Fault Tolerance Crash Test ---
if [ "$1" == "--crash-test" ]; then
    echo -e "\n⚠️ CRASH TEST MODE ENABLED."
    echo "The CLI Alert Subscriber will be forcefully killed in 30 seconds."
    
    sleep 30
    echo -e "\n💥 KILLING ALERT SUBSCRIBER (PID: $SUB_PID)..."
    kill -9 $SUB_PID
    
    echo "⏳ Waiting 10 seconds. Check your dashboard—the Broker is now queueing messages for the offline client..."
    sleep 10
    
    echo "🔄 RESTARTING ALERT SUBSCRIBER to trigger durable queue replay..."
    python -m demo.alert_subscriber &
    SUB_PID=$! # Update PID so cleanup still works
fi

# Keep the script running and wait for user to press Ctrl+C
wait