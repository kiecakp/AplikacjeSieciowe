"""
Kod klient ado testownia
"""

import socket

HOST = '127.0.0.1'
PORT = 9007
MSG_LEN = 20

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    for msg in ["krotka", "dokladnie dwadziesci", "za dluga wiadomosc!!!"]:
        # wysyłanie - dopełnij spacjami do 20 bajtów lub przytnij
        data = msg.encode('utf-8')[:MSG_LEN].ljust(MSG_LEN)
        s.sendall(data)
        print(f"Wysłano  ({len(data)}B): '{data.decode('utf-8')}'")

        # odbieranie - pętla gwarantuje dokładnie 20 bajtów
        response = b''
        while len(response) < MSG_LEN:
            chunk = s.recv(MSG_LEN - len(response))
            if not chunk:
                raise ConnectionError("Serwer rozłączył się")
            response += chunk

        print(f"Odebrano ({len(response)}B): '{response.decode('utf-8')}'")
        print()