"""
Napisz program klienta, który połączy się z wybranym serwerem POP3, a następnie wyświetli wszystkie
wiadomości znajdujące się w skrzynce.
"""

import socket

# Konfiguracja połączenia
HOST = 'interia.pl'
PORT = 110
USER = 'pasinf2017@interia.pl'
PASS = 'P4SInf2017'


class POP3Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """Nawiązuje połączenie z serwerem i odbiera powitanie."""
        self.sock.connect((self.host, self.port))
        greeting = self._recv_line()
        if not greeting.startswith('+OK'):
            raise ConnectionError(f"Serwer odrzucił połączenie: {greeting}")
        print(f"Połączono z {self.host}:{self.port}")
        return greeting

    def login(self, user, password):
        """Autoryzacja - wysyła USER i PASS."""
        response = self._send_command(f'USER {user}')
        if not response.startswith('+OK'):
            raise PermissionError(f"Błąd USER: {response}")

        response = self._send_command(f'PASS {password}')
        if not response.startswith('+OK'):
            raise PermissionError(f"Błąd PASS: {response}")

        print("Zalogowano pomyślnie.")

    def list_messages(self):
        """
        Wysyła komendę LIST.
        Zwraca listę krotek (numer, rozmiar) dla każdej wiadomości.
        """
        first_line = self._send_command('LIST')
        if not first_line.startswith('+OK'):
            raise RuntimeError(f"Błąd LIST: {first_line}")

        messages = []
        for line in self._recv_multiline():
            parts = line.split()
            if len(parts) == 2:
                messages.append((int(parts[0]), int(parts[1])))

        return messages

    def retrieve_message(self, num):
        """
        Wysyła komendę RETR <num>.
        Zwraca treść wiadomości jako listę linii.
        """
        first_line = self._send_command(f'RETR {num}')
        if not first_line.startswith('+OK'):
            raise RuntimeError(f"Błąd RETR {num}: {first_line}")

        return self._recv_multiline()

    def quit(self):
        """Kończy sesję POP3."""
        self._send_command('QUIT')
        self.sock.close()
        print("Rozłączono.")

    def _recv_line(self):
        """Odbiera jedną linię odpowiedzi zakończoną CRLF."""
        response = b''
        while not response.endswith(b'\r\n'):
            chunk = self.sock.recv(1)
            if not chunk:
                break
            response += chunk
        return response.decode('utf-8', errors='replace').strip()

    def _send_command(self, command):
        """Wysyła komendę do serwera POP3 (dodaje CRLF)."""
        self.sock.sendall((command + '\r\n').encode('utf-8'))
        return self._recv_line()

    def _recv_multiline(self):
        """
        Odbiera wieloliniową odpowiedź serwera POP3.
        Odpowiedź kończy się linią zawierającą samą kropkę '.'
        """
        lines = []
        while True:
            line = self._recv_line()
            if line == '.':
                break
            lines.append(line)
        return lines


def display_message(num, size, content):
    """Wyświetla pojedynczą wiadomość z podziałem na nagłówki i treść."""
    print(f"\n{'=' * 60}")
    print(f" WIADOMOŚĆ NR {num}  ({size} B)")
    print(f"{'=' * 60}")

    # Rozdziel nagłówki od treści - separatorem jest pusta linia
    separator = content.index('') if '' in content else len(content)
    headers = content[:separator]
    body = content[separator + 1:] if separator < len(content) else []

    # Wyświetl wybrane nagłówki
    important_headers = ('From:', 'To:', 'Subject:', 'Date:')
    print("--- NAGŁÓWKI ---")
    for line in headers:
        if line.startswith(important_headers):
            print(line)

    print("\n--- TREŚĆ ---")
    if body:
        print('\n'.join(body))
    else:
        print("(brak treści)")

    print(f"{'=' * 60}")


def main():
    client = POP3Client(HOST, PORT)

    try:
        client.connect()
        client.login(USER, PASS)

        # Krok 1: pobierz listę wszystkich wiadomości
        messages = client.list_messages()

        if not messages:
            print("Skrzynka jest pusta.")
            return

        print(f"\nSkrzynka zawiera {len(messages)} wiadomości. Pobieram...\n")

        # Krok 2: pobierz i wyświetl każdą wiadomość po kolei
        for i, (num, size) in enumerate(messages, start=1):
            print(f"Pobieranie wiadomości {i}/{len(messages)} (nr {num}, {size} B)...",
                  end='\r')
            content = client.retrieve_message(num)
            display_message(num, size, content)

        print(f"\nWyświetlono wszystkie {len(messages)} wiadomości.")

    except (ConnectionError, PermissionError, RuntimeError) as e:
        print(f"Błąd: {e}")
    finally:
        client.quit()


if __name__ == '__main__':
    main()