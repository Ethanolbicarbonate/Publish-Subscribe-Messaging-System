"""
Web Dashboard Server.
Serves the decoupled Publisher Control Center and Subscriber Hub.
"""
import eventlet
eventlet.monkey_patch()

import subprocess
from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO
from common.constants import DASHBOARD_PORT

# Import our new decoupled backend subscribers
from dashboard.subscribers.visualizer import VisualizerSubscriber
from dashboard.subscribers.alert_monitor import AlertMonitorSubscriber
from dashboard.subscribers.audit_log import AuditLogSubscriber
from dashboard.subscribers.broker_metrics import BrokerMetricsSubscriber

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pubsub-secret-key'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

dashboard_subscribers = {}

# --- Routes ---

@app.route('/')
def index():
    """Redirect root to the subscriber hub."""
    from flask import redirect
    return redirect('/subscribers')

@app.route('/subscribers')
def subscribers_hub():
    """Serves the main Hub showing Charts, Alerts, and the Firehose."""
    return render_template('subscribers.html')

@app.route('/publishers')
def publishers_control():
    """Serves the Control Center for triggering system events."""
    return render_template('publishers.html')

@app.route('/api/trigger_crash', methods=['POST'])
def trigger_crash_api():
    """REST endpoint triggered by the Control Center to spawn a Crash Publisher."""
    data = request.json
    topic = data.get("topic", "MARKET.CRYPTO.BTC")
    price = str(data.get("price", "60000"))
    drop = str(data.get("drop", "30"))
    
    print(f"[Dashboard API] 💥 Spawning Crash Simulator for {topic}...")
    
    # Spawn the crash_publisher as an entirely separate background process
    # This proves the dashboard isn't doing the publishing directly!
    subprocess.Popen([
        "python", "-m", "demo.crash_publisher", 
        topic, price, drop
    ])
    
    return jsonify({"status": "success", "message": f"Crash publisher spawned for {topic}"})

@app.route('/api/subscribers/status')
def subscribers_status_api():
    return jsonify({
        subscriber_id: {
            "connected": backend.subscriber.connected,
            "running": backend.subscriber.running,
        }
        for subscriber_id, backend in dashboard_subscribers.items()
    })

@app.route('/api/subscriber/<subscriber_id>/<action>', methods=['POST'])
def subscriber_control_api(subscriber_id, action):
    backend = dashboard_subscribers.get(subscriber_id)
    if backend is None:
        abort(404, description="Subscriber not found")

    if action == "disconnect":
        backend.subscriber.stop()
        # Ensure the client is fully marked offline in case of race conditions
        backend.subscriber.running = False
        backend.subscriber.connected = False
        if getattr(backend.subscriber, 'sock', None):
            try:
                backend.subscriber.sock.close()
            except Exception:
                pass
            backend.subscriber.sock = None
        return jsonify({"status": "success", "subscriber_id": subscriber_id, "connected": False})

    if action == "reconnect":
        if backend.subscriber.running and backend.subscriber.connected:
            return jsonify({"status": "success", "subscriber_id": subscriber_id, "connected": True, "message": "Already connected"})

        eventlet.spawn(backend.start)
        return jsonify({"status": "success", "subscriber_id": subscriber_id, "connected": False, "message": "Reconnect started"})

    abort(400, description="Unsupported action")

# --- WebSocket Handlers ---

@socketio.on('connect')
def handle_connect():
    print("[Dashboard UI] 🌐 Browser connected to WebSocket.")

# --- Server Startup ---

def run_dashboard():
    print(f"[Dashboard Server] Starting on port {DASHBOARD_PORT}...")
    
    # 1. Initialize the independent subscriber backends, passing them the socket interface
    vis_sub = VisualizerSubscriber(socketio)
    alert_sub = AlertMonitorSubscriber(socketio)
    audit_sub = AuditLogSubscriber(socketio)
    metrics_sub = BrokerMetricsSubscriber(socketio)

    dashboard_subscribers.update({
        vis_sub.subscriber.client_id: vis_sub,
        alert_sub.subscriber.client_id: alert_sub,
        audit_sub.subscriber.client_id: audit_sub,
        metrics_sub.subscriber.client_id: metrics_sub,
    })
    
    # 2. Spawn them as background eventlet threads
    eventlet.spawn(vis_sub.start)
    eventlet.spawn(alert_sub.start)
    eventlet.spawn(audit_sub.start)
    eventlet.spawn(metrics_sub.start)
    
    # 3. Start the Flask web server
    socketio.run(app, host='0.0.0.0', port=DASHBOARD_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_dashboard()