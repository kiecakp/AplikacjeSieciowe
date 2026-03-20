"""
Kod klienta do testowania
"""

import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(('127.0.0.1', 9001))
    for msg in ['Hello, Server!', 'How are you?', 'Goodbye!']:
        s.sendall(msg.encode('utf-8'))
        data = s.recv(1024)
        print(f"Otrzymano: {data.decode('utf-8')}")