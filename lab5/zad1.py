"""
Pod adresem 212.182.24.27 na porcie TCP o numerze 2912 działa serwer losujący 
liczby. Napisz program klienta, który będzie pobierał od użytkownika liczbę, 
a następnie będzie wysyłał ją do serwera w celu odgadnięcia wylosowanej przez 
serwer liczby. Po wysłaniu liczby klient powienien odbierać od serwera
odpowiedź mówiącą o tym, czy udało nam się daną liczbę odgadnąć.
"""

import socket

HOST = '212.182.24.27'
PORT = 2912
# Do testowania zadania 2
# HOST = '127.0.0.1'
# PORT = 9999

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Połączono z serwerem losującym liczby: {HOST}:{PORT}")

        # odbierz powitanie od serwera
        try:
            s.settimeout(2)
            welcome = s.recv(1024)
            if welcome:
                print("Serwer:", welcome.decode('utf-8', errors='ignore').strip())
        except socket.timeout:
            pass
        s.settimeout(None)

        while True:
            try:
                liczba = input("Podaj liczbę (lub 'exit' aby zakończyć): ")
            except EOFError:
                break

            if liczba.lower() == 'exit':
                print("Zakończono połączenie.")
                break

            try:
                int(liczba)
            except ValueError:
                print("Proszę podać poprawną liczbę.")
                continue

            # wysyłanie liczby do serwera
            s.sendall((liczba + '\n').encode('utf-8'))

            # odbieranie odpowiedzi od serwera
            odpowiedz = s.recv(1024)
            if not odpowiedz:
                print("Serwer zakończył połączenie.")
                break

            print("Serwer:", odpowiedz.decode('utf-8', errors='ignore').strip())

if __name__ == "__main__":
    main()