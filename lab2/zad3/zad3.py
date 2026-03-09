"""
Napisz program klienta, ktory polaczy sie z serwerem TCP dzialajacym
pod adresem 212.182.24.27 na porcie 2900, a nastepnie bedzie w petli
wysylal do niego tekst wczytany od uzytkownika, i odbieral odpowiedz.
"""

# tak samo jak w poprzednim zadaniu, serwer jest na 127.0.0.1

import socket

serwer_address = ('127.0.0.1', 2900)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(serwer_address)
        print("Polaczono z serwerem!")

        while True:
            message = input("Wpisz tekst do wyslania (lub 'exit' aby zakonczyc): ")
            if message.lower() == 'exit':
                print("Polaczenie zakonczone.")
                break

            s.sendall(message.encode())
            data = s.recv(1024)
            print("Odpowiedz z serwera:", data.decode())
except Exception as e:
    print("Nie mozna polaczyc sie z serwerem:", e)