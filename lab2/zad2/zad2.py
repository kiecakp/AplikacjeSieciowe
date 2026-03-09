"""
Napisz program klienta, ktory polaczy sie z serwerem TCP dzialajacym
pod adresem 212.182.24.27 na porcie 2900, a nastepnie wysle do niego
wiadomosc i odbierze odpowiedz.
"""

import socket

# patrzac na kod serwera to chyba chodzilo o adres: 127.0.0.1
serwer_address = ('127.0.0.1', 2900)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(serwer_address)
        print("Polaczono z serwerem!")

        message = "Hello :3"
        s.sendall(message.encode())
        data = s.recv(1024)
        print("Odpowiedz z serwera:", data.decode())
except Exception as e:
    print("Nie mozna polaczyc sie z serwerem:", e)