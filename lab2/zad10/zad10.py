"""
Napisz program klienta, ktory polaczy sie z serwerem UDP dzialajacym
pod adresem 212.182.24.27 na porcie 2907, a nastepnie przesle do serwera
nazwe hostname i odbierze odpowiadajace mu adres IP.
"""

# tak jak w poprzednim zadaniu serwer dziala na 127.0.0.1

import socket

serwer_address = ('127.0.0.1', 2907)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        hostname = input("Podaj nazwe hosta: ")
        s.sendto(hostname.encode(), serwer_address)

        data = s.recv(1024)
        print("Odpowiedz serwera: ", data.decode())
except Exception as e:
    print("Wystapil blad: ", e)