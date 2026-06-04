"""
Napisz program klienta, który połączy się z serwerem IMAP, a następnie wyświetli informację o tym, ile
wiadomości znajduje się we wszystkich skrzynkach łącznie.
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


def parse_mailboxes(resp):
    """
    Parsuje odpowiedź LIST i zwraca listę nazw skrzynek.
    Format linii: * LIST (\HasNoChildren) "/" INBOX
    """
    mailboxes = []
    for line in resp:
        if not line.upper().startswith("* LIST"):
            continue
        # Nazwa skrzynki to ostatni token w linii (może być w cudzysłowach)
        # Przykłady:
        #   * LIST (\HasNoChildren) "/" INBOX
        #   * LIST (\HasNoChildren) "/" "Sent Messages"
        #   * LIST (\Noselect) "/" "[Gmail]"
        parts = line.split('"')
        # Separator jest w cudzysłowach (np. "/"), nazwa skrzynki może też być
        # Bezpieczniej: weź wszystko po ostatnim separatorze-separatora
        # Strategia: split po spacji od końca, uwzględniając cudzysłowy
        stripped = line.strip()
        # Znajdź część po atrybutach: "* LIST (atrybuty) sep nazwa"
        # Atrybuty są w nawiasach (), potem separator, potem nazwa
        after_attrs = stripped[stripped.index(')') + 1:].strip()
        # after_attrs = '"/" INBOX' lub '"/" "Sent Messages"' lub 'NIL INBOX'
        tokens = after_attrs.split(None, 1)  # ["NIL" lub "\"/\"", "nazwa"]
        if len(tokens) < 2:
            continue
        name = tokens[1].strip().strip('"')
        mailboxes.append(name)
    return mailboxes


def parse_message_count(resp, mailbox_name):
    """
    Parsuje odpowiedź STATUS i zwraca liczbę wiadomości.
    Format: * STATUS INBOX (MESSAGES 5)
    """
    for line in resp:
        if not line.upper().startswith("* STATUS"):
            continue
        try:
            start = line.upper().index("MESSAGES") + len("MESSAGES")
            rest = line[start:].strip().strip(")").strip()
            return int(rest.split()[0])
        except (ValueError, IndexError):
            pass
    return None


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

    # Pobranie listy wszystkich skrzynek
    tag = send_command(sock, 'LIST "" "*"')
    resp = read_response(sock, tag)
    print()

    if get_status(resp, tag) != "OK":
        print("Błąd podczas pobierania listy skrzynek!")
        sock.close()
        return

    mailboxes = parse_mailboxes(resp)
    print(f"Znalezione skrzynki ({len(mailboxes)}): {mailboxes}\n")

    # Sprawdzenie liczby wiadomości w każdej skrzynce
    total = 0
    results = []

    for mailbox in mailboxes:
        tag = send_command(sock, f'STATUS "{mailbox}" (MESSAGES)')
        resp = read_response(sock, tag)
        print()

        if get_status(resp, tag) != "OK":
            print(f"  Pominięto skrzynkę '{mailbox}' (brak dostępu lub błąd).\n")
            continue

        count = parse_message_count(resp, mailbox)
        if count is not None:
            results.append((mailbox, count))
            total += count
        else:
            print(f"  Nie udało się odczytać liczby wiadomości dla '{mailbox}'.\n")

    # Podsumowanie
    print("")
    print("PODSUMOWANIE")
    for mailbox, count in results:
        print(f"  {mailbox:<30} {count:>5} wiadomości")
    print("")
    print(f"  {'ŁĄCZNIE':<30} {total:>5} wiadomości")
    print("")

    # Wylogowanie
    print()
    tag = send_command(sock, "LOGOUT")
    read_response(sock, tag)
    sock.close()
    print("Połączenie zamknięte.")


if __name__ == "__main__":
    main()