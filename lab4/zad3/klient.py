"""
Kod klienta do testowania
"""

import socket

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(5)
    for msg in ["Hello, Server!", "How are you?", "Goodbye!"]:
        s.sendto(msg.encode('utf-8'), ('127.0.0.1', 9002))
        response, _ = s.recvfrom(1024)
        print(f"Otrzymano od serwera: {response.decode('utf-8')}")