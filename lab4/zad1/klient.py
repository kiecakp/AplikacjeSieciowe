"""
Kod klienta do testow
"""

import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(('127.0.0.1', 9000))
    s.sendall("podaj czas".encode('utf-8'))
    response = s.recv(1024)
    print(f"Otrzymano od serwera: {response.decode('utf-8')}")