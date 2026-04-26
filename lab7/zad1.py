"""
Uwaga W poniższych zadaniach zakładamy, iż serwer powinien obsługiwać tylko jednego klienta w danej chwili.
Do wykonania zadań możesz wykorzystać konta pocztowe:
• Serwer interia.pl, port 110, konto: pas2017@interia.pl z hasłem P4SInf2017 (webmail: https://poczta.interia.pl/)
• Serwer interia.pl, port 110, konto: pasinf2017@interia.pl z hasłem P4SInf2017 (webmail: https://poczta.interia.pl/)
• Serwer 212.182.24.27, port 110, konto: pasinf2017@infumcs.edu z hasłem P4SInf2017 (webmail: https://212.182.24.27:443)
• Serwer 212.182.24.27, port 110, konto: pasinf@infumcs.edu z hasłem P4SInf2017 (webmail: https://212.182.24.27:443)
• Serwer 212.182.24.27, port 110, konto: pasumcs@infumcs.edu z hasłem P4SInf2017 (webmail: https://212.182.24.27:443)

Wykorzystując protokół telnet, oraz wybrany serwer POP3, sprawdź, ile wiadomości znajduje się w skrzynce.
"""

import socket

HOST = "interia.pl"
PORT = 110
USER = "pasinf2017@interia.pl"
PASS = "P4SInf2017"

def recv_line(sock):
    # Odbieranie linii zakończonej CRLF
    response = b""
    while not response.endswith(b"\r\n"):
        chunk = sock.recv(1)
        if not chunk:
            break
        response += chunk
    return response.decode('utf-8', errors='replace').strip()

def send_command(sock, command):
    # Wysyłanie komendy do serwera POP3 (zakończonej CRLF)
    sock.sendall((command + "\r\n").encode('utf-8'))
    return recv_line(sock)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print(f"Łączenie z serwerem {HOST}:{PORT}...")
        sock.connect((HOST, PORT))
        
        # Odbierz powitanie serwera
        greeting = recv_line(sock)
        print(f"Serwer: {greeting}")
        
        if not greeting.startswith('+OK'):
            print("Błąd: Serwer nie odpowiedział poprawnie.")
            return
 
        # Autoryzacja - wysyłanie loginu
        response = send_command(sock, f'USER {USER}')
        print(f"USER: {response}")
        if not response.startswith('+OK'):
            print("Błąd: Nieprawidłowa odpowiedź na USER.")
            return
 
        # Autoryzacja - wysyłanie hasła
        response = send_command(sock, f'PASS {PASS}')
        print(f"PASS: {response}")
        if not response.startswith('+OK'):
            print("Błąd: Nieprawidłowe hasło lub login.")
            return
 
        # Komenda STAT - zwraca liczbę wiadomości i łączny rozmiar
        response = send_command(sock, 'STAT')
        print(f"STAT: {response}")
 
        # Parsowanie odpowiedzi STAT: "+OK <liczba_wiadomości> <rozmiar>"
        if response.startswith('+OK'):
            parts = response.split()
            if len(parts) >= 3:
                num_messages = int(parts[1])
                total_size = int(parts[2])
                print()
                print("=" * 40)
                print(f"Liczba wiadomości w skrzynce: {num_messages}")
                print(f"Łączny rozmiar: {total_size} bajtów")
                print("=" * 40)
            else:
                print("Błąd: Nieoczekiwany format odpowiedzi STAT.")
        else:
            print(f"Błąd: {response}")
 
        # Zakończenie sesji
        response = send_command(sock, 'QUIT')
        print(f"QUIT: {response}")
 
if __name__ == '__main__':
    main()