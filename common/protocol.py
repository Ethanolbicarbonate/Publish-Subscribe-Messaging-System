"""
TCP Framing and Serialization layer.
Implements a 4-byte length-prefix framing protocol to safely send
JSON payloads over continuous TCP streams.
"""

import socket
import json
import struct
from common.message import Message
from common.constants import HEADER_LENGTH, ENCODING

def send_message(sock: socket.socket, message: Message) -> bool:
    """
    Serializes a message to JSON, prefixes it with a 4-byte length header,
    and sends it over the socket.
    """
    try:
        # 1. Serialize to JSON and encode to bytes
        json_data = json.dumps(message.to_dict())
        payload_bytes = json_data.encode(ENCODING)
        
        # 2. Pack the length of the payload into a 4-byte big-endian integer ('!I')
        header = struct.pack('!I', len(payload_bytes))
        
        # 3. Send header + payload over the socket
        sock.sendall(header + payload_bytes)
        return True
    except (socket.error, Exception) as e:
        print(f"[Protocol Error] Failed to send message: {e}")
        return False

def recv_message(sock: socket.socket) -> Message | None:
    """
    Reads the 4-byte header, determines payload length, and reads
    the exact payload bytes to reconstruct the Message.
    """
    try:
        # 1. Read exactly the header length (4 bytes)
        header_bytes = _recv_all(sock, HEADER_LENGTH)
        if not header_bytes:
            return None
            
        # 2. Unpack the header to get payload length
        payload_length = struct.unpack('!I', header_bytes)[0]
        
        # 3. Read exactly the payload length
        payload_bytes = _recv_all(sock, payload_length)
        if not payload_bytes:
            return None
            
        # 4. Decode bytes and reconstruct the Message
        json_data = payload_bytes.decode(ENCODING)
        msg_dict = json.loads(json_data)
        return Message.from_dict(msg_dict)
    except (socket.error, struct.error) as e:
        # Normal connection drops
        return None
    except json.JSONDecodeError as e:
        print(f"[Protocol Error] Received corrupted JSON payload: {e}")
        return None
    except Exception as e:
        print(f"[Protocol Error] Unexpected failure during recv: {e}")
        return None

def _recv_all(sock: socket.socket, n: int) -> bytes | None:
    """
    Helper function to reliably receive exactly `n` bytes from a TCP socket.
    Because TCP is a stream, a single `recv` might return fewer bytes than requested.
    """
    data = bytearray()
    while len(data) < n:
        try:
            packet = sock.recv(n - len(data))
            if not packet:
                # Socket closed by the other side
                return None
            data.extend(packet)
        except socket.error:
            return None
    return bytes(data)

# --- Loopback Test ---
if __name__ == "__main__":
    from common.constants import TYPE_PUBLISH
    print("Running Protocol Loopback Test...")
    
    # Create an in-memory pair of connected sockets
    sock1, sock2 = socket.socketpair()
    
    # Create a test message
    original_msg = Message(
        type=TYPE_PUBLISH,
        topic="STOCK.AAPL",
        payload={"price": 189.50, "volume": 3200}
    )
    
    print(f"Original Message: {original_msg.to_dict()}")
    
    # Simulate sender sending over sock1
    send_success = send_message(sock1, original_msg)
    print(f"Send Successful: {send_success}")
    
    # Simulate receiver receiving over sock2
    received_msg = recv_message(sock2)
    
    if received_msg:
        print(f"Received Message: {received_msg.to_dict()}")
        assert original_msg.msg_id == received_msg.msg_id
        assert original_msg.payload["price"] == received_msg.payload["price"]
        print("Protocol Loopback Test Passed! Encode -> Decode works perfectly.")
    else:
        print("Protocol Loopback Test Failed!")
        
    sock1.close()
    sock2.close()