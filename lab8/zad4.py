"""
Napisz program klienta, który połączy się z serwerem IMAP, a następnie sprawdzi, 
czy w skrzynce są nieprzeczytane wiadomości. Jeśli tak, wyświetli treść wszystkich 
nieprzeczytanych wiadomości oraz oznaczy je jako przeczytane (komenda STORE i flagi - FLAGS).
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


def read_fetch_response(sock, tag):
    """
    Czyta odpowiedź FETCH, która może zawierać dane binarne o określonej długości.
    Serwer sygnalizuje długość ciała w formacie {N} - literał IMAP.
    Np.: * 1 FETCH (BODY[TEXT] {36}\r\n<36 bajtów danych>\r\n)
    """
    response_lines = []
    buffer = b""

    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer += chunk

        # Przetwarzaj bufor linia po linii
        while b"\r\n" in buffer:
            line, rest = buffer.split(b"\r\n", 1)
            decoded = line.decode(errors="replace")

            # Sprawdź czy linia kończy się literałem {N}
            if decoded.rstrip().endswith("}") and "{" in decoded:
                try:
                    literal_len = int(decoded[decoded.rindex("{") + 1:-1])
                    print(f"<<< {decoded}")
                    response_lines.append(decoded)

                    # Czytaj dokładnie literal_len bajtów jako treść
                    buffer = rest
                    while len(buffer) < literal_len:
                        buffer += sock.recv(4096)

                    body_bytes = buffer[:literal_len]
                    buffer = buffer[literal_len:]
                    body_text = body_bytes.decode(errors="replace")

                    print(f"<<< [TREŚĆ WIADOMOŚCI ({literal_len} bajtów)]")
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


def parse_unread_ids(resp):
    """
    Parsuje odpowiedź SEARCH UNSEEN.
    Format: * SEARCH 1 3 5
    Zwraca listę ID nieprzeczytanych wiadomości.
    """
    for line in resp:
        if line.upper().startswith("* SEARCH"):
            parts = line.split()
            ids = [int(p) for p in parts[2:] if p.isdigit()]
            return ids
    return []


def extract_body(fetch_lines):
    """
    Wyciąga treść wiadomości z listy linii odpowiedzi FETCH.
    Szuka linii po literale {N}, która zawiera właściwą treść.
    """
    body_parts = []
    capture = False
    for line in fetch_lines:
        # Linia z literałem - następna jest treścią
        if "{" in line and "}" in line and "FETCH" in line.upper():
            capture = True
            continue
        if capture:
            body_parts.append(line)
            capture = False
    return "\n".join(body_parts).strip()


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

    # Wyszukiwanie nieprzeczytanych wiadomości
    tag = send_command(sock, "SEARCH UNSEEN")
    resp = read_response(sock, tag)
    print()

    if get_status(resp, tag) != "OK":
        print("Błąd podczas wyszukiwania nieprzeczytanych wiadomości!")
        sock.close()
        return

    unread_ids = parse_unread_ids(resp)

    if not unread_ids:
        print("Brak nieprzeczytanych wiadomości w skrzynce INBOX.")
        print()
        tag = send_command(sock, "LOGOUT")
        read_response(sock, tag)
        sock.close()
        print("Połączenie zamknięte.")
        return

    print(f"Nieprzeczytane wiadomości (ID): {unread_ids}")
    print(f"Liczba nieprzeczytanych: {len(unread_ids)}\n")

    # Pobranie i wyświetlenie treści każdej nieprzeczytanej wiadomości
    for msg_id in unread_ids:
        print("")
        print(f"WIADOMOŚĆ NR {msg_id}")
        print("")

        # Pobierz nagłówki
        tag = send_command(sock, f"FETCH {msg_id} BODY[HEADER.FIELDS (FROM SUBJECT DATE)]")
        resp = read_fetch_response(sock, tag)
        print()

        # Pobierz treść
        tag = send_command(sock, f"FETCH {msg_id} BODY[TEXT]")
        resp = read_fetch_response(sock, tag)
        body = extract_body(resp)
        print()

        print(f"--- Treść wiadomości nr {msg_id} ---")
        print(body if body else "(brak treści)")
        print()

    # Oznaczenie wszystkich nieprzeczytanych jako przeczytane
    # Budujemy zakres: np. "1,3,5" lub "1:5"
    ids_str = ",".join(str(i) for i in unread_ids)
    print("")
    print(f"Oznaczanie wiadomości ({ids_str}) jako przeczytane...")

    tag = send_command(sock, f"STORE {ids_str} +FLAGS \\Seen")
    resp = read_response(sock, tag)
    print()

    if get_status(resp, tag) == "OK":
        print(f"✓ Wiadomości {ids_str} zostały oznaczone jako przeczytane (\\Seen).\n")
    else:
        print(f"✗ Błąd podczas oznaczania wiadomości.\n")

    # Weryfikacja - ponowne wyszukanie nieprzeczytanych
    tag = send_command(sock, "SEARCH UNSEEN")
    resp = read_response(sock, tag)
    remaining = parse_unread_ids(resp)
    print()

    if not remaining:
        print("✓ Brak nieprzeczytanych wiadomości - wszystkie oznaczone jako przeczytane.")
    else:
        print(f"Pozostałe nieprzeczytane wiadomości: {remaining}")

    # Wylogowanie
    print()
    tag = send_command(sock, "LOGOUT")
    read_response(sock, tag)
    sock.close()
    print("\nPołączenie zamknięte.")


if __name__ == "__main__":
    main()