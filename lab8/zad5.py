"""
Napisz program klienta, który połączy się z serwerem IMAP, a następnie fizycznie usunie wybraną wiadomość.
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


def parse_all_ids(resp):
    # Parsuje odpowiedź SEARCH ALL i zwraca listę ID wiadomości.
    for line in resp:
        if line.upper().startswith("* SEARCH"):
            parts = line.split()
            return [int(p) for p in parts[2:] if p.isdigit()]
    return []


def read_fetch_response(sock, tag):
    # Czyta odpowiedź FETCH z obsługą literałów IMAP {N}.
    response_lines = []
    buffer = b""

    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer += chunk

        while b"\r\n" in buffer:
            line, rest = buffer.split(b"\r\n", 1)
            decoded = line.decode(errors="replace")

            # Obsługa literału {N} - następuje po nim blok danych o długości N
            if decoded.rstrip().endswith("}") and "{" in decoded:
                try:
                    literal_len = int(decoded[decoded.rindex("{") + 1:-1])
                    print(f"<<< {decoded}")
                    response_lines.append(decoded)
                    buffer = rest
                    while len(buffer) < literal_len:
                        buffer += sock.recv(4096)
                    body_bytes = buffer[:literal_len]
                    buffer = buffer[literal_len:]
                    body_text = body_bytes.decode(errors="replace")
                    print(f"<<< {body_text}")
                    response_lines.append(body_text)
                    continue
                except (ValueError, IndexError):
                    pass

            print(f"<<< {decoded}")
            response_lines.append(decoded)
            buffer = rest

            if decoded.startswith(tag):
                return response_lines

    return response_lines


def show_messages(sock, msg_ids):
    # Wyświetla skróconą listę wiadomości (ID + nagłówki From/Subject).
    print(f"\n{'ID':<6} {'Od':<30} {'Temat'}")
    print("-" * 70)
    for msg_id in msg_ids:
        tag = send_command(sock, f"FETCH {msg_id} BODY[HEADER.FIELDS (FROM SUBJECT)]")
        resp = read_fetch_response(sock, tag)

        from_val = ""
        subject_val = ""
        for line in resp:
            if line.upper().startswith("FROM:"):
                from_val = line[5:].strip()[:28]
            elif line.upper().startswith("SUBJECT:"):
                subject_val = line[8:].strip()[:35]

        print(f"{msg_id:<6} {from_val:<30} {subject_val}")
    print()


def main():
    print(f"Łączenie z {HOST}:{PORT}...")
    sock = socket.create_connection((HOST, PORT))

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

    # Wybór skrzynki INBOX
    tag = send_command(sock, "SELECT INBOX")
    resp = read_response(sock, tag)
    if get_status(resp, tag) != "OK":
        print("Błąd podczas wyboru skrzynki INBOX!")
        sock.close()
        return
    print()

    # Pobranie wszystkich wiadomości
    tag = send_command(sock, "SEARCH ALL")
    resp = read_response(sock, tag)
    print()

    all_ids = parse_all_ids(resp)

    if not all_ids:
        print("Skrzynka INBOX jest pusta - brak wiadomości do usunięcia.")
        tag = send_command(sock, "LOGOUT")
        read_response(sock, tag)
        sock.close()
        print("Połączenie zamknięte.")
        return

    # Wyświetlenie listy wiadomości
    print(f"Wiadomości w skrzynce INBOX ({len(all_ids)} szt.):")
    show_messages(sock, all_ids)

    # Wybór wiadomości do usunięcia
    while True:
        try:
            choice = input(f"Podaj ID wiadomości do usunięcia {all_ids}: ").strip()
            msg_id = int(choice)
            if msg_id in all_ids:
                break
            else:
                print(f"ID {msg_id} nie istnieje. Wybierz spośród: {all_ids}")
        except ValueError:
            print("Podaj liczbę całkowitą.")

    print()

    # Krok 1: Oznacz wiadomość flagą \Deleted
    print("")
    print(f"Krok 1: Oznaczanie wiadomości nr {msg_id} flagą \\Deleted...")
    tag = send_command(sock, f"STORE {msg_id} +FLAGS \\Deleted")
    resp = read_response(sock, tag)
    print()

    if get_status(resp, tag) != "OK":
        print("Błąd podczas ustawiania flagi \\Deleted!")
        sock.close()
        return

    print(f"✓ Flaga \\Deleted ustawiona na wiadomości nr {msg_id}.\n")

    # Krok 2: Fizyczne usunięcie wiadomości komendą EXPUNGE
    print("")
    print("Krok 2: Fizyczne usuwanie (EXPUNGE)...")
    tag = send_command(sock, "EXPUNGE")
    resp = read_response(sock, tag)
    print()

    if get_status(resp, tag) != "OK":
        print("Błąd podczas wykonywania EXPUNGE!")
        sock.close()
        return

    print(f"✓ Wiadomość nr {msg_id} została fizycznie usunięta ze skrzynki.\n")

    # Weryfikacja: sprawdź ile wiadomości pozostało
    print("")
    print("Weryfikacja - wiadomości pozostałe w INBOX:")
    tag = send_command(sock, "SEARCH ALL")
    resp = read_response(sock, tag)
    remaining_ids = parse_all_ids(resp)
    print()

    if not remaining_ids:
        print("Skrzynka INBOX jest teraz pusta.")
    else:
        print(f"Pozostałe wiadomości ({len(remaining_ids)} szt.): {remaining_ids}")

    # Wylogowanie
    print()
    tag = send_command(sock, "LOGOUT")
    read_response(sock, tag)
    sock.close()
    print("\nPołączenie zamknięte.")


if __name__ == "__main__":
    main()