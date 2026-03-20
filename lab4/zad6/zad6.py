"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie UDP, dla podłączającego się klienta, odbierze od niego 
nazwę hostname, i odeśle odpowiadający mu adres IP.
"""

#!/usr/bin/env python

import socket

HOST = '127.0.0.1'
PORT = 9005

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))

print(f"Serwer HOSTNAME->IP UDP nasluchuje na {HOST}:{PORT}")

try:
    while True:
        data, address = server.recvfrom(1024)
        hostname = data.decode('utf-8').strip()
        print(f"Otrzymano hostname: {hostname} od {address}")

        try:
            ip = socket.gethostbyname(hostname)
            response = ip
        except socket.gaierror:
            response = f"Error: Nie można znaleźć adresu IP dla {hostname}"

        server.sendto(response.encode('utf-8'), address)
        print(f"Wysłano odpowiedź: {response.encode('utf-8')} do {address}")

finally:
    server.close()