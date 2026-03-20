"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie UDP, dla podłączającego się klienta, odbierze od niego 
wiadomość o treści podanej w zadaniu nr 13 z laboratorium nr 3, a następnie 
odeśle klientowi odpowiedź TAK lub NIE. W przypadku błędnego sformatowania 
wiadomości, serwer odeśle klientowi odpowiedź BAD SYNTAX.

Treść z zadania 13:
Poniżej znajduje się pełny zapis segmentu TCP w postaci szesnastkowej 
(pole opcji ma 12 bajtów).
    0b 54 89 8b 1f 9a 18 ec bb b1 64 f2 80 18
    00 e3 67 71 00 00 01 01 08 0a 02 c1 a4 ee
    00 1a 4c ee 68 65 6c 6c 6f 20 3a 29
"""

#!/usr/bin/env python

import socket

HOST = '127.0.0.1'
PORT = 9008

def check_syntax(txt):
    tmp = txt.split(";")
    if len(tmp) != 7:
        return "BAD SYNTAX"
    
    if tmp[0] == "zad13odp" and tmp[1] == "src" and tmp[3] == "dst" and tmp[5] == "data":
        try:
            src_port = int(tmp[2])
            dst_port = int(tmp[4])
            data = tmp[6]

            if src_port == 2900 and dst_port == 35211 and data == "hello :)":
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
        msg= data.decode('utf-8').strip()
        print(f"Odebrano od {address}: {msg}")

        answer = check_syntax(msg)
        server.sendto(answer.encode('utf-8'), address)
        print(f"Wyslano do {address}: {answer}")

finally:
    server.close()