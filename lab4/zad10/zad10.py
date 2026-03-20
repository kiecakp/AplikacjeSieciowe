"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie UDP, dla podłączającego się klienta, odbierze od niego 
wiadomość o treści podanej w zadaniu nr 14 z laboratorium nr 3, a następnie 
odeśle klientowi odpowiedź TAK lub NIE. W przypadku błędnego sformatowania 
wiadomości, serwer odeśle klientowi odpowiedź BAD SYNTAX.

Treść z zadania 14:
Poniżej znajduje się pełny zapis datagramu UDP w postaci szesnastkowej.
    ed 74 0b 55 00 24 ef fd 70 72 6f 67 72 61
    6d 6d 69 6e 67 20 69 6e 20 70 79 74 68 6f
    6e 20 69 73 20 66 75 6e
"""

#!/usr/bin/env python

import socket

HOST = '127.0.0.1'
PORT = 9009

def check_syntax(txt):
    tmp = txt.split(";")
    if len(tmp) != 7:
        return "BAD SYNTAX"
    
    if tmp[0] == "zad14odp" and tmp[1] == "src" and tmp[3] == "dst" and tmp[5] == "data":
        try:
            src_port = int(tmp[2])
            dst_port = int(tmp[4])
            data = tmp[6]

            if src_port == 60788 and dst_port == 2901 and data == "programming in python is fun":
                return "TAK"
            else:
                return "NIE"
            
        except:
            return "BAD SYNTAX"
        
    return "BAD SYNTAX"

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))

print(f"Serwer UDP nasluchuje na {HOST}:{PORT}...")

try:
    while True:
        data, address = server.recvfrom(1024)
        msg = data.decode('utf-8').strip()
        print(f"Odebrano od {address}: {msg}")

        answer = check_syntax(msg)
        server.sendto(answer.encode('utf-8'), address)
        print(f"Wyslano do {address}: {answer}")

finally:
    server.close()