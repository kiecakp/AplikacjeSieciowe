"""
Zmodyfikuj program nr 2 z laboratorium nr 2 w ten sposób, aby klient 
wysłał i odebrał od serwera wiadomość o maksymalnej długości 20 znaków. 
Serwer TCP odbierający i wysyłający wiadomości o długości 20 działa pod 
adresem 212.182.24.27 na porcie 2908. Uwzględnij sytuacje, gdy:
    • wiadomość do wysłania jest za krótka - ma być wówczas uzupełniania 
      do 20 znaków znakami spacji
    • wiadomość do wysłania jest za długa - ma być przycięta do 20 znaków
      (lub wysłana w całości - sprawdź, co się wówczas stanie)
"""

# tak jak w poprzednim zadaniu serwer jest na 127.0.0.1

import socket

serwer_address = ('127.0.0.1', 2908)
MAX_LENGTH = 20

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
        data = s.recv(20)
        print("Odpowiedz z serwera:", data.decode())
except Exception as e:
    print("Nie mozna polaczyc sie z serwerem:", e)