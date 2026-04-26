"""
Wykorzystując protokół telnet, oraz wybrany serwer POP3, sprawdź, ile bajtów zajmuje każda wiadomość
(z osobna) znajdująca się w skrzynce.
"""

import socket

# Konfiguracja połączenia
HOST = 'interia.pl'
PORT = 110
USER = 'pasinf2017@interia.pl'
PASS = 'P4SInf2017'


def recv_line(sock):
    """Odbiera jedną linię odpowiedzi zakończoną CRLF."""
    response = b''
    while not response.endswith(b'\r\n'):
        chunk = sock.recv(1)
        if not chunk:
            break
        response += chunk
    return response.decode('utf-8', errors='replace').strip()


def send_command(sock, command):
    """Wysyła komendę do serwera POP3 (dodaje CRLF)."""
    sock.sendall((command + '\r\n').encode('utf-8'))
    return recv_line(sock)


def recv_multiline(sock):
    """
    Odbiera wieloliniową odpowiedź serwera POP3.
    Odpowiedź kończy się linią zawierającą samą kropkę '.'
    """
    lines = []
    while True:
        line = recv_line(sock)
        if line == '.':
            break
        lines.append(line)
    return lines


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

        # Komenda LIST - zwraca listę wiadomości z ich rozmiarami
        # Pierwsza linia: "+OK <liczba> messages (<łączny_rozmiar> octets)"
        # Następne linie: "<numer> <rozmiar>"
        # Ostatnia linia: "."
        first_line = send_command(sock, 'LIST')
        print(f"LIST: {first_line}")

        if not first_line.startswith('+OK'):
            print(f"Błąd: {first_line}")
            return

        # Odbierz pozostałe linie (po jednej na wiadomość)
        message_lines = recv_multiline(sock)

        # Parsowanie i wyświetlenie wyników
        print()
        print("=" * 40)
        print(f"{'Nr':>4}  {'Rozmiar (B)':>12}  {'Rozmiar (KB)':>12}")
        print("-" * 40)

        messages = []
        for line in message_lines:
            parts = line.split()
            if len(parts) == 2:
                num = int(parts[0])
                size = int(parts[1])
                messages.append((num, size))
                print(f"{num:>4}  {size:>12}  {size / 1024:>11.2f}")

        print("=" * 40)
        total = sum(size for _, size in messages)
        print(f"Łącznie: {len(messages)} wiadomości, {total} bajtów ({total / 1024:.2f} KB)")
        print("=" * 40)

        # Zakończenie sesji
        response = send_command(sock, 'QUIT')
        print(f"\nQUIT: {response}")


if __name__ == '__main__':
    main()