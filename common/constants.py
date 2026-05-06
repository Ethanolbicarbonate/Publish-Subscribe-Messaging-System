"""
Centralized constants for the Publish-Subscribe system.
This file defines network configurations, protocol settings, timeouts,
and system-wide enumerated states.
"""

import os

# Network
HOST = '127.0.0.1'
BROKER_PORT = 9999
DASHBOARD_PORT = 8080

# Protocol
HEADER_LENGTH = 4  
ENCODING = 'utf-8'

# Timeouts and Intervals
HEARTBEAT_INTERVAL = 10
MISSED_HEARTBEATS_LIMIT = 2
RETRY_INTERVAL = 5       
MAX_RETRIES = 3

# Persistence
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'persistence', 'pubsub.db')

# Message Types
TYPE_PUBLISH = 'PUBLISH'
TYPE_SUBSCRIBE = 'SUBSCRIBE'
TYPE_UNSUBSCRIBE = 'UNSUBSCRIBE'
TYPE_ACK = 'ACK'
TYPE_HEARTBEAT = 'HEARTBEAT'
TYPE_CONNECTED = 'CONNECTED' 

# Message Delivery Statuses
STATUS_PENDING = 'PENDING'
STATUS_DELIVERED = 'DELIVERED'
STATUS_DEAD_LETTER = 'DEAD_LETTER'

# Message Types
TYPE_CONNECT = 'CONNECT'
TYPE_PUBLISH = 'PUBLISH'