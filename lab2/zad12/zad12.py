"""
Funkcje recv i send nie gwarantują wysłania / odbioru wszystkich danych. 
Rozważmy funkcję recv. Przykładowo, 100 bajtów może zostać wysłane jako 
grupa po 10 bajtów, albo od razu w całości. Oznacza to, iż jeśli używamy 
gniazd TCP, musimy odbierać dane, dopóki nie mamy pewności, że odebraliśmy
odpowiednią ich ilość. Zmodyfikuj program nr 11 z laboratorium nr 2 w ten
sposób, aby mieć pewność, że klient w rzeczywistości odebrał / wysłał 
wiadomość o wymaganej długości.
"""

import socket

serwer_address = ('127.0.0.1', 2908)
MAX_LENGTH = 20

def recvall(sock, msgLen):
    msg = b""
    bytesRcvd = 0

    while bytesRcvd < msgLen:

        chunk = sock.recv(msgLen - bytesRcvd)

        if not chunk:
            break

        bytesRcvd += len(chunk)
        msg += chunk

    return msg

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(serwer_address)
        print("Polaczono z serwerem!")

        message = input("Wpisz wiadomosc (max 20 znakow): ")

        if len(message) < MAX_LENGTH:
            message = message.ljust(MAX_LENGTH)
        elif len(message) > MAX_LENGTH:
            message = message[:MAX_LENGTH]

        s.sendall(message.encode())
        data = recvall(s, MAX_LENGTH)
        print("Odpowiedz z serwera:", data.decode())
except Exception as e:
    print("Nie mozna polaczyc sie z serwerem:", e)