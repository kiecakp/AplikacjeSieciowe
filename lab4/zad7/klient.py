"""
Kod klienta do testowania
"""

import socket

HOST = '127.0.0.1'
PORT = 9006

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    for msg in [
        "krotka",
        "dokladnie dwadziesci",   # 20 znaków ASCII
        "ta wiadomosc jest za dluga i zostanie przycieta"
    ]:
        s.sendall(msg.encode('utf-8'))
        response = s.recv(20)
        print(f"Wysłano  : {msg}")
        print(f"Odebrano : {response.decode('utf-8')}")
        print()