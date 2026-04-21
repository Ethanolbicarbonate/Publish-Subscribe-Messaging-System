"""
Web Dashboard Server.
Uses Flask to serve the frontend and Flask-SocketIO to stream
real-time Pub/Sub events to connected browsers.
"""
import eventlet
# Patch standard library to be non-blocking for eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from common.constants import DASHBOARD_PORT

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pubsub-secret-key'
# Use eventlet for async WebSocket operations, allow CORS for local dev
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Shared state to track broker metrics 
# (This will be updated by the Dashboard Subscriber in the next subphase)
broker_stats = {
    "connected_clients": 0,
    "active_topics": 0,
    "messages_delivered": 0,
    "pending_acks": 0
}

@app.route('/')
def index():
    """Serves the main dashboard HTML page."""
    # Note: index.html doesn't exist yet, we will build it in Subphase 6.3
    return render_template('index.html')

@app.route('/api/status')
def status():
    """REST endpoint returning current broker statistics as JSON."""
    return jsonify(broker_stats)

@socketio.on('connect')
def handle_connect():
    """Triggered when a new browser opens the dashboard."""
    print("[Dashboard UI] 🌐 A browser connected to the live feed.")

@socketio.on('disconnect')
def handle_disconnect():
    """Triggered when a browser closes the dashboard."""
    print("[Dashboard UI] 🌐 A browser disconnected.")

def run_dashboard():
    """Starts the Flask-SocketIO server."""
    print(f"[Dashboard Server] Starting on port {DASHBOARD_PORT}...")
    # use_reloader=False is important here so it doesn't spawn duplicate processes
    socketio.run(app, host='0.0.0.0', port=DASHBOARD_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_dashboard()