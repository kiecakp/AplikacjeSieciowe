"""
Napisz program klienta, który połączy się z wybranym serwerem POP3, a następnie wyświetli informację
o tym, ile wiadomości znajduje się w skrzynce.
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

    def stat(self):
        """
        Wysyła komendę STAT.
        Zwraca krotkę (liczba_wiadomości, łączny_rozmiar).
        """
        response = self._send_command('STAT')
        if not response.startswith('+OK'):
            raise RuntimeError(f"Błąd STAT: {response}")

        parts = response.split()
        num_messages = int(parts[1])
        total_size = int(parts[2])
        return num_messages, total_size

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


def main():
    client = POP3Client(HOST, PORT)

    try:
        client.connect()
        client.login(USER, PASS)

        # Pobranie liczby wiadomości
        num_messages, total_size = client.stat()

        print()
        print("=" * 40)
        print(f"  Liczba wiadomości w skrzynce: {num_messages}")
        print("=" * 40)

    except (ConnectionError, PermissionError, RuntimeError) as e:
        print(f"Błąd: {e}")
    finally:
        client.quit()


if __name__ == '__main__':
    main()