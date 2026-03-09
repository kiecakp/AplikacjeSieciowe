"""
Napisz peogram klienta, ktory polaczy sie z serwerem UDP dzialajacym 
pod adresem 212.182.24.27 na porcie 2902, a nastepnie przesle do serwera
liczbe, operator, liczbe (pobrane od uzytkownika) i odbierze odpowiedz.
"""

# tak samo jak w poprzednim zadaniu, serwer jest na 127.0.0.1

import socket

serwer_address = ('127.0.0.1', 2902)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        first_number = input("Podaj pierwsza liczbe: ")
        operator = input("Podaj operator: ")
        second_number = input("Podaj druga liczbe: ")

        s.sendto(first_number.encode(), serwer_address)
        s.sendto(operator.encode(), serwer_address)
        s.sendto(second_number.encode(), serwer_address)
        data = s.recvfrom(1024)
        
        print(f"Odpowiedz od serwera: {data[0].decode()}")
except Exception as e:
    print(f"Wystapil blad: {e}")