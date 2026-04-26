"""
Centralized constants for the Publish-Subscribe system.
This file defines network configurations, protocol settings, timeouts,
and system-wide enumerated states.
"""

import os

# --- Network Constants ---
HOST = '127.0.0.1'
BROKER_PORT = 9999
DASHBOARD_PORT = 8080

# --- Protocol Constants ---
# We use a 4-byte big-endian integer to prefix all messages with their length.
HEADER_LENGTH = 4  
ENCODING = 'utf-8'

# --- Timeouts and Intervals (seconds) ---
HEARTBEAT_INTERVAL = 10
MISSED_HEARTBEATS_LIMIT = 2
# At-least-once delivery retry settings
RETRY_INTERVAL = 5       
MAX_RETRIES = 3

# --- Persistence ---
# Resolve the base directory dynamically to ensure SQLite creates the DB in the right place
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'persistence', 'pubsub.db')

# --- Message Types ---
TYPE_PUBLISH = 'PUBLISH'
TYPE_SUBSCRIBE = 'SUBSCRIBE'
TYPE_UNSUBSCRIBE = 'UNSUBSCRIBE'
TYPE_ACK = 'ACK'
TYPE_HEARTBEAT = 'HEARTBEAT'
# Control message sent by broker upon successful connection
TYPE_CONNECTED = 'CONNECTED' 

# --- Message Delivery Statuses ---
STATUS_PENDING = 'PENDING'
STATUS_DELIVERED = 'DELIVERED'
# DEAD_LETTER implies the message exhausted retries and the subscriber is unreachable
STATUS_DEAD_LETTER = 'DEAD_LETTER'

# --- Demo Alert Thresholds ---
ALERT_HIGH_THRESH = 200.0
ALERT_LOW_THRESH = 50.0