"""
Napisz program klienta, który połączy się z serwerem IMAP, a następnie wyświetli informację o tym, ile
wiadomości znajduje się w skrzynce Inbox.
"""

import socket

HOST = "212.182.24.27"
PORT = 143
USERNAME = "pasumcs@infumcs.edu"
PASSWORD = "P4SInf2017"

tag_counter = 0


def next_tag():
    global tag_counter
    tag_counter += 1
    return f"A{tag_counter:04d}"


def send_command(sock, command):
    tag = next_tag()
    full_cmd = f"{tag} {command}\r\n"
    print(f">>> {full_cmd}", end="")
    sock.sendall(full_cmd.encode())
    return tag


def read_response(sock, tag):
    # Czyta linie odpowiedzi serwera aż do linii zaczynającej się od naszego tagu.
    response_lines = []
    buffer = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer += chunk
        while b"\r\n" in buffer:
            line, buffer = buffer.split(b"\r\n", 1)
            decoded = line.decode(errors="replace")
            print(f"<<< {decoded}")
            response_lines.append(decoded)
            if decoded.startswith(tag):
                return response_lines
    return response_lines


def read_greeting(sock):
    # Odczytuje wiadomość powitalną serwera.
    buffer = b""
    while True:
        chunk = sock.recv(4096)
        buffer += chunk
        if b"\r\n" in buffer:
            line, _ = buffer.split(b"\r\n", 1)
            decoded = line.decode(errors="replace")
            print(f"<<< {decoded}")
            return decoded


def get_status(lines, tag):
    # Zwraca status odpowiedzi serwera (OK / NO / BAD).
    for line in lines:
        if line.startswith(tag):
            parts = line.split(" ", 2)
            if len(parts) >= 2:
                return parts[1]
    return None


def main():
    print(f"Łączenie z {HOST}:{PORT}...")
    sock = socket.create_connection((HOST, PORT))

    # Powitanie serwera
    read_greeting(sock)
    print()

    # Logowanie
    tag = send_command(sock, f"LOGIN {USERNAME} {PASSWORD}")
    resp = read_response(sock, tag)
    if get_status(resp, tag) != "OK":
        print("Błąd logowania!")
        sock.close()
        return
    print()

    # STATUS INBOX - pobierz liczbę wiadomości
    tag = send_command(sock, "STATUS INBOX (MESSAGES)")
    resp = read_response(sock, tag)
    print()

    if get_status(resp, tag) != "OK":
        print("Błąd podczas pobierania statusu skrzynki INBOX!")
        sock.close()
        return

    # Parsowanie odpowiedzi: * STATUS INBOX (MESSAGES 5)
    message_count = None
    for line in resp:
        if line.upper().startswith("* STATUS"):
            # Wyciągnij liczbę z "MESSAGES <n>"
            try:
                start = line.upper().index("MESSAGES") + len("MESSAGES")
                rest = line[start:].strip().strip("()").strip()
                message_count = int(rest.split()[0])
            except (ValueError, IndexError):
                pass

    if message_count is not None:
        print(f"Liczba wiadomości w skrzynce INBOX: {message_count}")
    else:
        print("Nie udało się odczytać liczby wiadomości.")

    # Wylogowanie
    print()
    tag = send_command(sock, "LOGOUT")
    read_response(sock, tag)
    sock.close()
    print("Połączenie zamknięte.")


if __name__ == "__main__":
    main()