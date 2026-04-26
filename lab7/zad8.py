"""
Napisz program klienta, który połączy się z wybranym serwerem POP3, a następnie wyświetli informację
o tym, ile bajtów zajmuje każda wiadomość (z osobna) znajdująca się w skrzynce.
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

        # Odbierz wieloliniową odpowiedź aż do kropki
        messages = []
        for line in self._recv_multiline():
            parts = line.split()
            if len(parts) == 2:
                num = int(parts[0])
                size = int(parts[1])
                messages.append((num, size))

        return messages

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


def main():
    client = POP3Client(HOST, PORT)

    try:
        client.connect()
        client.login(USER, PASS)

        messages = client.list_messages()

        if not messages:
            print("Skrzynka jest pusta.")
            return

        print()
        print("=" * 45)
        print(f"{'Nr':>4}  {'Rozmiar (B)':>12}  {'Rozmiar (KB)':>12}")
        print("-" * 45)
        for num, size in messages:
            print(f"{num:>4}  {size:>12}  {size / 1024:>11.2f}")
        print("-" * 45)

        total = sum(size for _, size in messages)
        print(f"{'SUMA':>4}  {total:>12}  {total / 1024:>11.2f}")
        print("=" * 45)
        print(f"Łącznie {len(messages)} wiadomości")

    except (ConnectionError, PermissionError, RuntimeError) as e:
        print(f"Błąd: {e}")
    finally:
        client.quit()


if __name__ == '__main__':
    main()