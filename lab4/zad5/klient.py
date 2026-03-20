"""
Kod klienta do testowania
"""

import socket

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(5)
    for ip in ["8.8.8.8", "1.1.1.1", "127.0.0.1", "999.999.999.999"]:
        s.sendto(ip.encode('utf-8'), ('127.0.0.1', 9004))
        response, _ = s.recvfrom(1024)
        print(f"Hostname dla {ip}: {response.decode('utf-8')}")