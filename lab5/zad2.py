"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na określonym 
porcie TCP będzie losował liczbę i odbierał od klienta wiadomości. W przypadku, 
gdy w wiadomości klient przyśle do serwera coś innego, niż liczbę, serwer powinien 
poinformować klienta o błędzie. Po odebraniu liczby od klienta, serwer sprawdza, 
czy otrzymana liczba jest:
    • mniejsza od wylosowanej przez serwer
    • równa wylosowanej przez serwer
    • większa od wylosowanej przez serwer
A następnie odsyła stosowną informację do klienta. W przypadku, gdy klient odgadnie 
liczbę, serwer powinien zakończyć działanie.
"""

import socket
import random

HOST = '127.0.0.1'
PORT = 9999

def main():
    wylosowana = random.randint(1, 100)
    print(f"[Serwer] Wylosowana liczba: {wylosowana}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"[Serwer] Oczekiwanie na połączenie na {HOST}:{PORT}...")

        conn, addr = s.accept()
        with conn:
            print(f"[Serwer] Połączono z klientem: {addr}")
            conn.sendall("Zgadnij liczbe od 1 do 100\n".encode('utf-8'))

            while True:
                data = conn.recv(1024)
                if not data:
                    print("[Serwer] Klient rozłączył się.")
                    break

                message = data.decode('utf-8', errors='ignore').strip()
                print(f"[Serwer] Otrzymano od klienta: {message}")

                try:
                    liczba = int(message)
                except ValueError:
                    conn.sendall("Błąd: Proszę podać poprawną liczbę.\n".encode('utf-8'))
                    continue

                if liczba < wylosowana:
                    conn.sendall("Za mało.\n".encode('utf-8'))
                elif liczba > wylosowana:
                    conn.sendall("Za dużo.\n".encode('utf-8'))
                else:
                    conn.sendall("Gratulacje! Odgadłeś liczbę!\n".encode('utf-8'))
                    print("[Serwer] Klient odgadł liczbę. Zakończenie działania serwera.")
                    break

if __name__ == "__main__":
    main()