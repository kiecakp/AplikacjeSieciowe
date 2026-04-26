"""
Wykorzystując protokół telnet, oraz wybrany serwer POP3, usuń wiadomość o najmniejszym rozmiarze.
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

        # Autoryzacja
        response = send_command(sock, f'USER {USER}')
        print(f"USER: {response}")
        if not response.startswith('+OK'):
            print("Błąd: Nieprawidłowa odpowiedź na USER.")
            return

        response = send_command(sock, f'PASS {PASS}')
        print(f"PASS: {response}")
        if not response.startswith('+OK'):
            print("Błąd: Nieprawidłowe hasło lub login.")
            return

        # Krok 1: Pobierz listę wiadomości z rozmiarami (LIST)
        first_line = send_command(sock, 'LIST')
        print(f"LIST: {first_line}")

        if not first_line.startswith('+OK'):
            print(f"Błąd: {first_line}")
            return

        message_lines = recv_multiline(sock)

        # Krok 2: Znajdź wiadomość o najmniejszym rozmiarze
        messages = []
        for line in message_lines:
            parts = line.split()
            if len(parts) == 2:
                num = int(parts[0])
                size = int(parts[1])
                messages.append((num, size))

        if not messages:
            print("Skrzynka jest pusta.")
            return

        print("\nLista wiadomości:")
        print(f"{'Nr':>4}  {'Rozmiar (B)':>12}")
        print("-" * 20)
        for num, size in messages:
            print(f"{num:>4}  {size:>12}")

        smallest_num, smallest_size = min(messages, key=lambda x: x[1])
        print(f"\nNajmniejsza wiadomość: nr {smallest_num}, rozmiar: {smallest_size} bajtów")

        # Krok 3: Potwierdzenie przed usunięciem
        confirm = input(f"\nCzy na pewno chcesz usunąć wiadomość nr {smallest_num} ({smallest_size} B)? [t/N]: ")
        if confirm.strip().lower() != 't':
            print("Anulowano usuwanie.")
            send_command(sock, 'QUIT')
            return

        # Krok 4: Usuń wiadomość (DELE)
        # Uwaga: DELE tylko oznacza wiadomość do usunięcia.
        # Faktyczne usunięcie następuje dopiero po wysłaniu QUIT.
        response = send_command(sock, f'DELE {smallest_num}')
        print(f"DELE {smallest_num}: {response}")

        if response.startswith('+OK'):
            print(f"\nWiadomość nr {smallest_num} została oznaczona do usunięcia.")
            print("Zostanie trwale usunięta po zakończeniu sesji (QUIT).")
        else:
            print(f"Błąd podczas usuwania: {response}")

        # Krok 5: Zakończenie sesji - tutaj następuje faktyczne usunięcie
        response = send_command(sock, 'QUIT')
        print(f"\nQUIT: {response}")
        print("Sesja zakończona. Wiadomość została trwale usunięta.")


if __name__ == '__main__':
    main()