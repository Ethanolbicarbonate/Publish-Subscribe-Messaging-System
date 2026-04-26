import socket
import time
import uuid
import sqlite3
import sys
import os

# Append parent directory to system path for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import send_message, recv_message
from common.message import Message
from common.constants import HOST, BROKER_PORT, TYPE_PUBLISH, TYPE_SUBSCRIBE, DB_PATH

def connect_client(client_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, BROKER_PORT))
    handshake = Message(type='CONNECT', payload={"client_id": client_id})
    send_message(s, handshake)
    
    # Discard the welcome transmission
    recv_message(s) 
    return s

def run_test():
    print("1. Client initialization.")
    sub_id = "dashboard_" + str(uuid.uuid4())[:8]
    pub_id = "rgb_sensor_" + str(uuid.uuid4())[:8]
    
    sub_socket = connect_client(sub_id)
    pub_socket = connect_client(pub_id)
    
    print("2. Topic subscription.")
    sub_msg = Message(type=TYPE_SUBSCRIBE, topic="facility.line_1.#")
    send_message(sub_socket, sub_msg)
    time.sleep(0.5)
    
    print("3. Payload transmission.")
    msg_id = str(uuid.uuid4())
    payload = {
        "sensor_type": "standard_RGB_optical",
        "grade_classification": "Class I",
        "lenticel_damage_percentage": 35,
        "standard_applied": "40% lenticel exception" 
    }
    pub_msg = Message(
        type=TYPE_PUBLISH, 
        topic="facility.line_1.grade.class_I", 
        payload=payload,
        msg_id=msg_id
    )
    send_message(pub_socket, pub_msg)
    time.sleep(0.5)
    
    print("4. Receipt verification.")
    received = recv_message(sub_socket)
    if received and received.msg_id == msg_id:
        print(" -> Success: Message routed properly.")
    else:
        print(" -> Failure: Message lost.")
        
    print("5. Database inspection.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    msg_row = conn.execute("SELECT * FROM messages WHERE msg_id = ?", (msg_id,)).fetchone()
    status_row = conn.execute("SELECT * FROM delivery_status WHERE msg_id = ? AND subscriber_id = ?", (msg_id, sub_id)).fetchone()
    
    if msg_row and status_row:
        print(" -> Success: Payload resides in 'messages', state resides in 'delivery_status'.")
    else:
        print(" -> Failure: Database normalization incorrect.")
        
    sub_socket.close()
    pub_socket.close()

if __name__ == "__main__":
    run_test()