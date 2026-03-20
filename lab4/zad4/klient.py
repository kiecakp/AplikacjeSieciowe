"""
Kod klienta do testowania
"""

import socket

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(5)
    for msg in ["10 + 5", "20 - 3", "7 * 8", "15 / 0", "abc + def"]:
        s.sendto(msg.encode('utf-8'), ('127.0.0.1', 9003))
        response, _ = s.recvfrom(1024)
        print(f"Wysłano: {msg}, Otrzymano: {response.decode('utf-8')}")