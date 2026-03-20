"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie UDP, dla podłączającego się klienta, odbierze od niego 
wiadomość o treści podanej w zadaniu nr 15 z laboratorium nr 3, a następnie 
odeśle klientowi odpowiedź TAK lub NIE. W przypadku błędnego sformatowania 
wiadomości, serwer odeśle klientowi odpowiedź BAD SYNTAX.

Treść z zadania 15:
Poniżej znajduje się pełny zapis pakietu IP w postaci szesnastkowej (bez 
pola opcji IP, jeśli protokół to TCP, pole opcji TCP ma 12 bajtów).
    45 00 00 4e f7 fa 40 00 38 06 9d 33 d4 b6 18 1b
    c0 a8 00 02 0b 54 b9 a6 fb f9 3c 57 c1 0a 06 c1
    80 18 00 e3 ce 9c 00 00 01 01 08 0a 03 a6 eb 01
    00 0b f8 e5 6e 65 74 77 6f 72 6b 20 70 72 6f 67
    72 61 6d 6d 69 6e 67 20 69 73 20 66 75 6e
"""

#!/usr/bin/env python

import socket

HOST = '127.0.0.1'
PORT = 9010

def check_message_A(txt):
    tmp = txt.split(";")
    if len(tmp) != 9:
        return "BAD SYNTAX"
    
    if tmp[0] == "zad15odpA" and tmp[1] == "ver" and tmp[3] == "srcip" and tmp[5] == "dstip" and tmp[7] == "type":
        try:
            ver = int(tmp[2])
            srcip = tmp[4]
            dstip = tmp[6]
            typ = int(tmp[8])

            if ver == 4 and typ == 6 and srcip == "212.182.24.27" and dstip == "192.168.0.2":
                return "TAK"
            else:
                return "NIE"
            
        except:
            return "BAD SYNTAX"
        
    return "BAD SYNTAX"

def check_message_B(txt):
    tmp = txt.split(";")
    if len(tmp) != 7:
        return "BAD SYNTAX"
    
    if tmp[0] == "zad15odpB" and tmp[1] == "srcport" and tmp[3] == "dstport" and tmp[5] == "data":
        try:
            srcport = int(tmp[2])
            dstport = int(tmp[4])
            data = tmp[6]

            if srcport == 2900 and dstport == 47526 and data == "network programming is fun":
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

        prefix = msg.split(";")[0]
        if prefix == "zad15odpA":
            answer = check_message_A(msg)
        elif prefix == "zad15odpB":
            answer = check_message_B(msg)
        else:
            answer = "BAD SYNTAX"

        server.sendto(answer.encode('utf-8'), address)
        print(f"Wyslano do {address}: {answer}")

finally:
    server.close()