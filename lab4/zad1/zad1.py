"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie TCP, dla podłączającego się klienta, będzie odsyłał mu 
aktualny czas oraz datę. Prawidłowa komunikacja powinna odbywać się w 
nastepujacy sposób:
    • Serwer odbiera od klienta wiadomość (dowolną)
    • Serwer odsyła klientowi aktualną datę i czas
"""

#!/usr/bin/env python

import socket
from time import ctime

HOST = '127.0.0.1'
PORT = 9000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)

print(f"Serwer TCP nasluchuje na {HOST}:{PORT}...")

try:
    while True:
        conn, address = server.accept()
        print(f"Polaczono z {address}")

        with conn:
            data = conn.recv(1024)
            if data:
                print(f"Odebrano: {data.decode('utf-8')}")
                now = ctime()
                conn.sendall(now.encode('utf-8'))
                print(f"Wyslano: {now}")

finally:
    server.close()
