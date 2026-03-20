"""
Kod klienta do testowania
"""

import socket

HOST = '127.0.0.1'
PORT = 9010

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(5)
    for msg in [
        "zad15odpA;ver;4;srcip;212.182.24.27;dstip;192.168.0.2;type;6",  # TAK
        "zad15odpA;ver;4;srcip;1.2.3.4;dstip;192.168.0.2;type;6",        # NIE
        "zad15odpB;srcport;2900;dstport;47526;data;network programming is fun",  # TAK
        "zad15odpB;srcport;1234;dstport;47526;data;network programming is fun",  # NIE
        "zupelnie zly format",                                            # BAD SYNTAX
    ]:
        s.sendto(msg.encode('utf-8'), (HOST, PORT))
        response, _ = s.recvfrom(1024)
        print(f"Wysłano : {msg}")
        print(f"Odebrano: {response.decode('utf-8')}")
        print()