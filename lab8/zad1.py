"""
Wykorzystując protokół telnet, oraz serwer IMAP, zaloguj się do skrzynki i sprawdź, ile wiadomości znajduje się w poszczególnych 
skrzynkach. Pobierz pierwszą dostępną wiadomość, i oznacz ją jako przeczytaną.
Wykorzystaj komendę protokołu IMAP - STORE.
"""

import socket
import ssl

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
    # Czytaj linie aż znajdziemy linię zaczynającą się od naszego tagu.
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
    buffer = b""
    while True:
        chunk = sock.recv(4096)
        buffer += chunk
        if b"\r\n" in buffer:
            line, _ = buffer.split(b"\r\n", 1)
            decoded = line.decode(errors="replace")
            print(f"<<< {decoded}")
            return decoded

def get_status_from_response(lines, tag):
    for line in lines:
        if line.startswith(tag):
            parts = line.split(" ", 2)
            if len(parts) >= 2:
                return parts[1]  # OK / NO / BAD
    return None

def main():
    print(f"Łączenie z {HOST}:{PORT}...\n")
    sock = socket.create_connection((HOST, PORT))

    # Odczytaj powitanie
    read_greeting(sock)
    print()

    # LOGIN
    tag = send_command(sock, f"LOGIN {USERNAME} {PASSWORD}")
    resp = read_response(sock, tag)
    status = get_status_from_response(resp, tag)
    if status != "OK":
        print("Błąd logowania!")
        sock.close()
        return
    print("\n✓ Zalogowano pomyślnie.\n")

    # LIST - pobierz wszystkie skrzynki
    print("")
    print("Pobieranie listy skrzynek...")
    tag = send_command(sock, 'LIST "" "*"')
    resp = read_response(sock, tag)
    print()

    # Wyciągnij nazwy skrzynek z odpowiedzi
    mailboxes = []
    for line in resp:
        if line.startswith("* LIST"):
            # Format: * LIST (\HasNoChildren) "/" INBOX
            parts = line.rsplit(" ", 1)
            if parts:
                name = parts[-1].strip().strip('"')
                mailboxes.append(name)

    print(f"\nZnalezione skrzynki: {mailboxes}\n")

    # Sprawdź liczbę wiadomości w każdej skrzynce
    print("")
    print("Liczba wiadomości w każdej skrzynce:")
    for mailbox in mailboxes:
        tag = send_command(sock, f'STATUS "{mailbox}" (MESSAGES UNSEEN)')
        resp = read_response(sock, tag)
        for line in resp:
            if line.startswith("* STATUS"):
                print(f"  → {line}")
        print()

    # SELECT INBOX i pobierz pierwszą wiadomość
    print("")
    print("Wybieranie skrzynki INBOX...")
    tag = send_command(sock, "SELECT INBOX")
    resp = read_response(sock, tag)
    print()

    # SEARCH ALL - sprawdź jakie wiadomości są w INBOX
    tag = send_command(sock, "SEARCH ALL")
    resp = read_response(sock, tag)
    print()

    message_ids = []
    for line in resp:
        if line.startswith("* SEARCH"):
            parts = line.split()
            # "* SEARCH 1 2 3 ..."
            ids = parts[2:]
            message_ids = [int(i) for i in ids if i.isdigit()]

    if not message_ids:
        print("Brak wiadomości w skrzynce INBOX.")
        tag = send_command(sock, "LOGOUT")
        read_response(sock, tag)
        sock.close()
        return

    print(f"Identyfikatory wiadomości w INBOX: {message_ids}\n")

    first_id = message_ids[0]

    # Pobierz treść pierwszej wiadomości
    print("")
    print(f"Pobieranie treści wiadomości nr {first_id}...")
    tag = send_command(sock, f"FETCH {first_id} BODY[]")
    resp = read_response(sock, tag)
    print()

    # Oznacz pierwszą wiadomość jako przeczytaną
    print("")
    print(f"Oznaczanie wiadomości nr {first_id} jako przeczytana (\\Seen)...")
    tag = send_command(sock, f"STORE {first_id} +FLAGS \\Seen")
    resp = read_response(sock, tag)
    status = get_status_from_response(resp, tag)
    if status == "OK":
        print(f"\n✓ Wiadomość nr {first_id} została oznaczona jako przeczytana.\n")
    else:
        print(f"\n✗ Nie udało się oznaczyć wiadomości. Status: {status}\n")

    # Sprawdź flagi wiadomości po zmianie
    print("")
    print("Sprawdzanie flag po zmianie:")
    tag = send_command(sock, f"FETCH {first_id} (FLAGS)")
    resp = read_response(sock, tag)
    print()

    # LOGOUT
    print("")
    tag = send_command(sock, "LOGOUT")
    read_response(sock, tag)
    sock.close()
    print("\nPołączenie zamknięte.")

if __name__ == "__main__":
    main()