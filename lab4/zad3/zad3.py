"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie UDP, dla podłączającego się klienta, będzie odsyłał mu 
przesłaną wiadomość (tzw. serwer echa). Prawidłowa komunikacja powinna 
odbywać się w nastepujacy sposób:
    • Serwer odbiera dane od klienta
    • Serwer odsyła klientowi odebrane od niego dane
"""

#!/usr/bin/env python

HOST = '127.0.0.1'
PORT = 9002

import socket

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))

print(f"Serwer ECHO UDP nasluchuje na {HOST}:{PORT}...")

try:
    while True:
        data, address = server.recvfrom(1024)
        print(f"Otrzymano dane od {address}: {data.decode('utf-8')}")
        server.sendto(data, address)
        print(f"Wysłano dane do {address}: {data.decode('utf-8')}")

finally:
    server.close()