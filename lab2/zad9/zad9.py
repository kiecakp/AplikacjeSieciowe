"""
Napisz program klienta, ktory polaczy sie z serwerem UDP dzialajacym pod
adresem 212.182.24.27 na porcie 2906, a nastepnie przesle do serwera
adres IP i odbierze odpowiadajaca mu nazwe hostname.
"""

# tak samo jak w poprzednim zadaniu, serwer jest na 127.0.0.1

import socket

serwer_address = ('127.0.0.1', 2906)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        message = '127.0.0.1'
        s.sendto(message.encode(), serwer_address)

        data, address = s.recvfrom(1024)
        print(f'Otrzymana nazwa hosta: {data.decode()}')

except Exception as e:
    print(f"Wystapil blad: {e}")