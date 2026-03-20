"""
Klient do testowania
"""

import socket

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(5)
    for host in ["google.com", "localhost", "nieistniejący.host"]:
        s.sendto(host.encode('utf-8'), ('127.0.0.1', 9005))
        response, _ = s.recvfrom(1024)
        print(f"{host} -> {response.decode('utf-8')}")