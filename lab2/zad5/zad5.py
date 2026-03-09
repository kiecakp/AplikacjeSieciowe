"""
Napisz program klienta, ktory polaczy sie z serwerem UDP dzialajacym
pod adresem 212.182.24.27 na porcie 2901, a nastepnie bedzie w petli
wysylal do niego tekst wczytany od uzytkownika i odbieral odpowiedz.
"""

# tak samo jak w poprzednim zadaniu, serwer jest na 127.0.0.1

import socket

serwer_address =('127.0.0.1', 2901)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        while True:
            message = input("Wpisz tekst do wyslania (lub 'exit' aby zakonczyc): ")
            if message.lower() == 'exit':
                print("Zakonczono polaczenie.")
                break

            s.sendto(message.encode(), serwer_address)
            data = s.recvfrom(1024)
            print("Odpowiedz z serwera:", data[0].decode())
except Exception as e:
    print("Nie mozna polaczyc sie z serwerem:", e)