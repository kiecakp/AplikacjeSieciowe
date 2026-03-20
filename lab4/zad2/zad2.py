"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie TCP, dla podłączającego się klienta, będzie odsyłał mu 
przesłaną wiadomość (tzw. serwer echa). Prawidłowa komunikacja powinna 
odbywać się w nastepujacy sposób:
    • Serwer odbiera dane od klienta
    • Serwer odsyła klientowi odebrane od niego dane
"""

#!/usr/bin/env python

import socket

HOST = '127.0.0.1'
PORT = 9001

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)

print(f"Serwer ECHO TCP nasluchuje na {HOST}:{PORT}...")

try:
    while True:
        conn, address = server.accept()
        print(f"Polaczono z {address}")

        while conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Otrzymano od {address}: {data.decode()}")
                conn.sendall(data)
                print(f"Wyslano do {address}: {data.decode()}")

finally:
    server.close()