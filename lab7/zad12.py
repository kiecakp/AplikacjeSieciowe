"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na określonym porcie TCP, będzie
serwerem poczty, obsługującym protokół POP3. Nie realizuj faktycznego pobierania e-maili, tylko zasymuluj jego działanie tak, żeby napisany wcześniej klient POP3 mógł pobrac wiadomosci. Pamiętaj o obsłudze
przypadku, gdy klient poda nie zaimplementowaną przez serwer komendę.
"""

import socket
import threading

# Konfiguracja serwera
HOST = '127.0.0.1'
PORT = 1100  # port > 1024 nie wymaga uprawnień roota

# Symulowane dane użytkowników: login -> hasło
USERS = {
    'pasinf2017@interia.pl': 'P4SInf2017',
    'testuser': 'testpass',
}

# Symulowane wiadomości w skrzynce
# Każda wiadomość to słownik z kluczami: size, content
MESSAGES = [
    {
        'size': 1321,
        'content': (
            "From: <sender1@example.com>\r\n"
            "To: <pasinf2017@interia.pl>\r\n"
            "Subject: Testowa wiadomosc 1\r\n"
            "Date: Thu, 6 Apr 2017 10:00:00 +0200\r\n"
            "\r\n"
            "Tresc pierwszej wiadomosci testowej.\r\n"
            "To jest symulowany serwer POP3.\r\n"
        ),
    },
    {
        'size': 1319,
        'content': (
            "From: <sender2@example.com>\r\n"
            "To: <pasinf2017@interia.pl>\r\n"
            "Subject: Testowa wiadomosc 2\r\n"
            "Date: Thu, 6 Apr 2017 11:00:00 +0200\r\n"
            "\r\n"
            "Tresc drugiej wiadomosci testowej.\r\n"
            "Protokol POP3 dziala poprawnie.\r\n"
        ),
    },
    {
        'size': 2376,
        'content': (
            "From: <sender3@example.com>\r\n"
            "To: <pasinf2017@interia.pl>\r\n"
            "Subject: Testowa wiadomosc 3 - najwieksza\r\n"
            "Date: Thu, 6 Apr 2017 12:00:00 +0200\r\n"
            "\r\n"
            "Tresc trzeciej wiadomosci testowej.\r\n"
            "Ta wiadomosc jest najwieksza.\r\n"
            "Serwer POP3 symuluje prawdziwy serwer pocztowy.\r\n"
            "Mozna ja pobrac komenda RETR 3.\r\n"
        ),
    },
]


class POP3Session:
    """
    Obsługuje pojedynczą sesję klienta POP3.
    Sesja przechodzi przez stany: AUTHORIZATION -> TRANSACTION -> UPDATE
    """

    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.state = 'AUTHORIZATION'
        self.username = None
        self.authenticated = False
        # Kopia wiadomości dla sesji - deleted to zbiór numerów oznaczonych do usunięcia
        self.messages = list(MESSAGES)
        self.deleted = set()

    def send(self, message):
        """Wysyła odpowiedź do klienta (dodaje CRLF)."""
        response = message + '\r\n'
        self.conn.sendall(response.encode('utf-8'))
        print(f"  [S] {message}")

    def recv_line(self):
        """Odbiera jedną linię komendy od klienta zakończoną CRLF."""
        data = b''
        while not data.endswith(b'\r\n'):
            chunk = self.conn.recv(1)
            if not chunk:
                break
            data += chunk
        line = data.decode('utf-8', errors='replace').strip()
        if line:
            print(f"  [C] {line}")
        return line

    def handle(self):
        """Główna pętla obsługi sesji."""
        print(f"\nNowe połączenie od {self.addr}")

        # Powitanie serwera
        self.send('+OK POP3 server ready (symulowany serwer)')

        while True:
            line = self.recv_line()
            if not line:
                print(f"Klient {self.addr} rozłączył się.")
                break

            # Rozdziel komendę i argumenty
            parts = line.split()
            command = parts[0].upper() if parts else ''
            args = parts[1:]

            # Obsługa komend w zależności od stanu sesji
            if command == 'QUIT':
                self.cmd_quit()
                break
            elif self.state == 'AUTHORIZATION':
                self.handle_authorization(command, args)
            elif self.state == 'TRANSACTION':
                self.handle_transaction(command, args)
            else:
                self.send('-ERR Nieznany stan sesji.')

        self.conn.close()
        print(f"Sesja z {self.addr} zakończona.")

    def handle_authorization(self, command, args):
        """Obsługuje komendy w stanie AUTHORIZATION."""
        if command == 'USER':
            if not args:
                self.send('-ERR Brak nazwy użytkownika.')
                return
            self.username = args[0]
            if self.username in USERS:
                self.send(f'+OK Witaj {self.username}, podaj hasło.')
            else:
                self.send('-ERR Nieznany użytkownik.')
                self.username = None

        elif command == 'PASS':
            if not self.username:
                self.send('-ERR Najpierw podaj USER.')
                return
            if not args:
                self.send('-ERR Brak hasła.')
                return
            password = args[0]
            if USERS.get(self.username) == password:
                self.authenticated = True
                self.state = 'TRANSACTION'
                total = sum(m['size'] for m in self.messages)
                self.send(f'+OK Zalogowano. Masz {len(self.messages)} wiadomości ({total} bajtów).')
            else:
                self.send('-ERR Nieprawidłowe hasło.')
                self.username = None

        else:
            self.send(f'-ERR Komenda {command} niedozwolona w stanie autoryzacji.')

    def handle_transaction(self, command, args):
        """Obsługuje komendy w stanie TRANSACTION."""
        if command == 'STAT':
            self.cmd_stat()
        elif command == 'LIST':
            self.cmd_list(args)
        elif command == 'RETR':
            self.cmd_retr(args)
        elif command == 'DELE':
            self.cmd_dele(args)
        elif command == 'NOOP':
            self.send('+OK')
        elif command == 'RSET':
            self.cmd_rset()
        else:
            # Obsługa niezaimplementowanej komendy
            self.send(f'-ERR Komenda {command} nie jest obsługiwana przez ten serwer.')

    def cmd_stat(self):
        """STAT - zwraca liczbę wiadomości i łączny rozmiar (bez usuniętych)."""
        active = [(i + 1, m) for i, m in enumerate(self.messages)
                  if (i + 1) not in self.deleted]
        count = len(active)
        total = sum(m['size'] for _, m in active)
        self.send(f'+OK {count} {total}')

    def cmd_list(self, args):
        """LIST [num] - lista wiadomości z rozmiarami."""
        if args:
            # LIST z numerem - zwraca rozmiar konkretnej wiadomości
            try:
                num = int(args[0])
                if num < 1 or num > len(self.messages):
                    self.send('-ERR Nie ma wiadomości o takim numerze.')
                    return
                if num in self.deleted:
                    self.send('-ERR Wiadomość została usunięta.')
                    return
                size = self.messages[num - 1]['size']
                self.send(f'+OK {num} {size}')
            except ValueError:
                self.send('-ERR Nieprawidłowy argument.')
        else:
            # LIST bez argumentu - zwraca całą listę
            active = [(i + 1, m) for i, m in enumerate(self.messages)
                      if (i + 1) not in self.deleted]
            total = sum(m['size'] for _, m in active)
            self.send(f'+OK {len(active)} wiadomości ({total} bajtów)')
            for num, msg in active:
                self.send(f'{num} {msg["size"]}')
            self.send('.')

    def cmd_retr(self, args):
        """RETR <num> - pobiera treść wiadomości."""
        if not args:
            self.send('-ERR Brak numeru wiadomości.')
            return
        try:
            num = int(args[0])
            if num < 1 or num > len(self.messages):
                self.send('-ERR Nie ma wiadomości o takim numerze.')
                return
            if num in self.deleted:
                self.send('-ERR Wiadomość została usunięta.')
                return
            msg = self.messages[num - 1]
            self.send(f'+OK {msg["size"]} bajtów')
            # Wyślij treść wiadomości linia po linii
            for line in msg['content'].splitlines():
                # Transparentność kropki: linie zaczynające się od '.' dostają dodatkową kropkę
                if line.startswith('.'):
                    self.conn.sendall(('.' + line + '\r\n').encode('utf-8'))
                else:
                    self.conn.sendall((line + '\r\n').encode('utf-8'))
            # Zakończ wieloliniową odpowiedź
            self.conn.sendall(b'.\r\n')
            print("  [S] .")
        except ValueError:
            self.send('-ERR Nieprawidłowy argument.')

    def cmd_dele(self, args):
        """DELE <num> - oznacza wiadomość do usunięcia."""
        if not args:
            self.send('-ERR Brak numeru wiadomości.')
            return
        try:
            num = int(args[0])
            if num < 1 or num > len(self.messages):
                self.send('-ERR Nie ma wiadomości o takim numerze.')
                return
            if num in self.deleted:
                self.send('-ERR Wiadomość już jest oznaczona do usunięcia.')
                return
            self.deleted.add(num)
            self.send(f'+OK Wiadomość {num} oznaczona do usunięcia.')
        except ValueError:
            self.send('-ERR Nieprawidłowy argument.')

    def cmd_rset(self):
        """RSET - cofa wszystkie oznaczenia do usunięcia."""
        self.deleted.clear()
        self.send(f'+OK Przywrócono {len(self.messages)} wiadomości.')

    def cmd_quit(self):
        """QUIT - kończy sesję i wykonuje faktyczne usunięcia (stan UPDATE)."""
        self.state = 'UPDATE'
        if self.deleted:
            print(f"  Usuwanie wiadomości: {sorted(self.deleted)}")
        self.send('+OK Do widzenia.')


def start_server():
    """Uruchamia serwer POP3 nasłuchujący na połączenia."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Pozwala na ponowne użycie portu po restarcie serwera
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(5)

    print(f"Symulowany serwer POP3 nasłuchuje na {HOST}:{PORT}")
    print(f"Dostępne konta: {list(USERS.keys())}")
    print(f"Liczba wiadomości: {len(MESSAGES)}")
    print("Naciśnij Ctrl+C aby zatrzymać serwer.\n")

    try:
        while True:
            conn, addr = server_sock.accept()
            # Każde połączenie obsługiwane w osobnym wątku
            session = POP3Session(conn, addr)
            thread = threading.Thread(target=session.handle, daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")
    finally:
        server_sock.close()


if __name__ == '__main__':
    start_server()