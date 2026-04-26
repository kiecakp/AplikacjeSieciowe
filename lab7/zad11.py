"""
Napisz program klienta, który połączy się z wybranym serwerem POP3, a następnie pobierze z serwera
wiadomość z załącznikiem (obrazkiem) i zapisze obrazek na dysk. Nazwa obrazka musi zgadzać się z nazwą
załącznika podaną w mailu. Pamiętaj, że do przesyłania załączników binarnych w poczcie elektronicznej
wykorzystywane jest kodowanie Base64.
"""

import socket
import base64
import os

# Konfiguracja połączenia
HOST = 'interia.pl'
PORT = 110
USER = 'pasinf2017@interia.pl'
PASS = 'P4SInf2017'

# Numer wiadomości z załącznikiem obrazka (zmień jeśli potrzeba)
MESSAGE_NUM = 1


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


def parse_mime_parts(lines):
    """
    Parsuje wiadomość MIME i zwraca listę części.
    Każda część to słownik z kluczami: headers, body, filename, encoding, content_type.
    """
    # Znajdź granicę MIME (boundary) w nagłówkach wiadomości
    boundary = None
    for line in lines:
        if 'boundary=' in line.lower():
            # Wytnij wartość boundary z nagłówka
            # Przykład: Content-Type: multipart/mixed; boundary="----=_Part_123"
            part = line.split('boundary=')[-1].strip().strip('"')
            boundary = part
            break

    if not boundary:
        raise ValueError("Nie znaleziono granicy MIME (boundary) w wiadomości. "
                         "Upewnij się, że wiadomość ma załącznik.")

    print(f"Znaleziono boundary MIME: {boundary}")

    # Podziel treść wiadomości na części MIME używając boundary
    full_text = '\n'.join(lines)
    raw_parts = full_text.split('--' + boundary)

    parts = []
    for raw_part in raw_parts:
        # Pomiń puste fragmenty i końcowy znacznik "--"
        raw_part = raw_part.strip()
        if not raw_part or raw_part == '--':
            continue

        part_lines = raw_part.splitlines()

        # Rozdziel nagłówki od treści części MIME (separator: pusta linia)
        separator = 0
        for i, line in enumerate(part_lines):
            if line.strip() == '':
                separator = i
                break

        part_headers = part_lines[:separator]
        part_body = part_lines[separator + 1:]

        # Odczytaj nagłówki tej części MIME
        content_type = ''
        content_encoding = ''
        filename = ''

        for header in part_headers:
            header_lower = header.lower()
            if header_lower.startswith('content-type:'):
                content_type = header.split(':', 1)[1].strip()
            elif header_lower.startswith('content-transfer-encoding:'):
                content_encoding = header.split(':', 1)[1].strip().lower()
            elif 'filename=' in header_lower:
                # Wytnij nazwę pliku z nagłówka Content-Disposition lub Content-Type
                # Przykład: Content-Disposition: attachment; filename="obrazek.png"
                filename = header.split('filename=')[-1].strip().strip('"')

        parts.append({
            'content_type': content_type,
            'encoding': content_encoding,
            'filename': filename,
            'body': part_body,
        })

    return parts


def find_and_save_image(parts):
    """
    Przeszukuje części MIME w poszukiwaniu załącznika obrazka.
    Dekoduje Base64 i zapisuje plik na dysk pod oryginalną nazwą.
    """
    image_types = ('image/jpeg', 'image/png', 'image/gif',
                   'image/bmp', 'image/webp', 'image/tiff')

    for part in parts:
        content_type = part['content_type'].lower()
        is_image = any(img_type in content_type for img_type in image_types)

        if not is_image:
            continue

        filename = part['filename']
        encoding = part['encoding']
        body = part['body']

        if not filename:
            # Jeśli brak nazwy pliku, wygeneruj nazwę na podstawie typu
            ext = content_type.split('/')[-1].split(';')[0].strip()
            filename = f"attachment.{ext}"
            print(f"Brak nazwy załącznika, użyto: {filename}")

        print(f"\nZnaleziono załącznik: {filename}")
        print(f"Typ: {content_type}")
        print(f"Kodowanie: {encoding}")

        if encoding != 'base64':
            print(f"Nieobsługiwane kodowanie: {encoding}")
            continue

        # Złącz linie base64 i zdekoduj
        base64_data = ''.join(body).replace('\r', '').replace('\n', '')

        try:
            image_data = base64.b64decode(base64_data)
        except Exception as e:
            print(f"Błąd dekodowania Base64: {e}")
            continue

        # Zapisz plik na dysk pod oryginalną nazwą z maila
        output_path = os.path.join(os.getcwd(), filename)
        with open(output_path, 'wb') as f:
            f.write(image_data)

        print(f"Zapisano obrazek: {output_path} ({len(image_data)} B)")
        return filename

    print("Nie znaleziono żadnego załącznika z obrazkiem w wiadomości.")
    return None


def main():
    client = POP3Client(HOST, PORT)

    try:
        client.connect()
        client.login(USER, PASS)

        # Pobierz listę wiadomości i znajdź wiadomość z załącznikiem
        messages = client.list_messages()
        if not messages:
            print("Skrzynka jest pusta.")
            return

        print(f"\nDostępne wiadomości: {[num for num, _ in messages]}")
        print(f"Pobieram wiadomość nr {MESSAGE_NUM}...\n")

        # Pobierz wskazaną wiadomość
        content = client.retrieve_message(MESSAGE_NUM)

        # Parsuj części MIME i znajdź obrazek
        try:
            parts = parse_mime_parts(content)
            print(f"Znaleziono {len(parts)} część/części MIME.")
            find_and_save_image(parts)
        except ValueError as e:
            print(f"Błąd parsowania MIME: {e}")

    except (ConnectionError, PermissionError, RuntimeError) as e:
        print(f"Błąd: {e}")
    finally:
        client.quit()


if __name__ == '__main__':
    main()