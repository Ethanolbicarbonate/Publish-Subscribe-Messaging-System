"""
Web Dashboard Server.
Serves the decoupled Publisher Control Center and Subscriber Hub.
"""
import eventlet
eventlet.monkey_patch()

import subprocess
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from common.constants import DASHBOARD_PORT

# Import our new decoupled backend subscribers
from dashboard.subscribers.visualizer import VisualizerSubscriber
from dashboard.subscribers.alert_monitor import AlertMonitorSubscriber
from dashboard.subscribers.audit_log import AuditLogSubscriber

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pubsub-secret-key'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

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
    
    # 2. Spawn them as background eventlet threads
    eventlet.spawn(vis_sub.start)
    eventlet.spawn(alert_sub.start)
    eventlet.spawn(audit_sub.start)
    
    # 3. Start the Flask web server
    socketio.run(app, host='0.0.0.0', port=DASHBOARD_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_dashboard()