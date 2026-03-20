"""
Kod klienta do testowania
"""

import socket

HOST = '127.0.0.1'
PORT = 9008

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(5)
    for msg in [
        "zad13odp;src;2900;dst;35211;data;hello :)",   # TAK
        "zad13odp;src;1234;dst;35211;data;hello :)",   # NIE
        "zad13odp;src;2900;dst;35211",                 # BAD SYNTAX
        "zupelnie zly format",                         # BAD SYNTAX
    ]:
        s.sendto(msg.encode('utf-8'), (HOST, PORT))
        response, _ = s.recvfrom(1024)
        print(f"Wysłano : {msg}")
        print(f"Odebrano: {response.decode('utf-8')}")
        print()