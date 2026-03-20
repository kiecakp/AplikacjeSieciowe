"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie UDP, dla podłączającego się klienta, odbierze od niego 
adres IP, i odeśle odpowiadającą mu nazwę hostname.
"""

#!/usr/bin/env python

import socket

HOST ='127.0.0.1'
PORT = 9004

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))

print(f"Serwer DNs LOOKUP UDP nasluchuje na {HOST}:{PORT}")

try:
    while True:
        data, address = server.recvfrom(1024)
        ip = data.decode('utf-8').strip()
        print(f"Odebrano od {address}: {ip}")

        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            response = hostname
        except socket.herror:
            response = f"Error: Nie znaleziono hostname dla IP {ip}"
        except socket.gaierror:
            response = f"Error: Nieprawidłowy adres IP {ip}"
        
        server.sendto(response.encode('utf-8'), address)
        print(f"Wysłano do {address}: {response}")
finally:
    server.close()