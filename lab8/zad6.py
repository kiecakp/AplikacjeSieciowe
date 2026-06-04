"""
Napisz program w pythonie serwera, który działając pod adresem 127.0.0.1 oraz na określonym porcie TCP, 
będzie serwerem poczty, obsługującym protokół IMAP. Nie realizuj faktycznego pobierania e-maili, tylko 
zasymuluj jego działanie tak, żeby napisany wcześniej klient IMAP mógł pobrac wiadomosci. Pamiętaj o 
obsłudze przypadku, gdy klient poda nie zaimplementowaną przez serwer komendę.
"""

import socket
import sys
import datetime

# Symulowane wiadomości w skrzynce INBOX
MESSAGES = [
    {
        "flags": r"\Seen",
        "date": "01-Jan-2025 10:00:00 +0100",
        "from": "alice@example.com",
        "to": "user@example.com",
        "subject": "Witaj!",
        "body": "Hej, to jest pierwsza wiadomosc testowa.\r\n",
    },
    {
        "flags": "",
        "date": "15-Mar-2025 14:30:00 +0100",
        "from": "bob@example.com",
        "to": "user@example.com",
        "subject": "Spotkanie",
        "body": "Przypominam o spotkaniu w piatek o 10:00.\r\nPozdrawiam,\r\nBob\r\n",
    },
    {
        "flags": "",
        "date": "01-Jun-2025 09:15:00 +0200",
        "from": "carol@example.com",
        "to": "user@example.com",
        "subject": "Oferta",
        "body": "Dzien dobry,\r\nPrzesylam oferte wspolpracy.\r\ncarol\r\n",
    },
]

VALID_USER = "pasinf2017@infumcs.edu"
VALID_PASS = "P4SInf2017"

# Pomocnicze: budowanie surowej wiadomości RFC 2822
def build_raw(msg: dict) -> str:
    header = (
        f"From: {msg['from']}\r\n"
        f"To: {msg['to']}\r\n"
        f"Subject: {msg['subject']}\r\n"
        f"Date: {msg['date']}\r\n"
        f"\r\n"
    )
    return header + msg["body"]


def build_envelope(uid: int, msg: dict) -> str:
    raw = build_raw(msg)
    size = len(raw.encode())
    flags = f"({msg['flags']})" if msg['flags'] else "()"
    # ENVELOPE: (date subject from sender reply-to to cc bcc in-reply-to message-id)
    envelope = (
        f'("{msg["date"]}" "{msg["subject"]}" '
        f'(("{msg["from"]}" NIL "{msg["from"].split("@")[0]}" "{msg["from"].split("@")[1]}")) '
        f'(("{msg["from"]}" NIL "{msg["from"].split("@")[0]}" "{msg["from"].split("@")[1]}")) '
        f'(("{msg["from"]}" NIL "{msg["from"].split("@")[0]}" "{msg["from"].split("@")[1]}")) '
        f'(("{msg["to"]}" NIL "{msg["to"].split("@")[0]}" "{msg["to"].split("@")[1]}")) '
        f'NIL NIL NIL "<msg{uid}@example.com>")'
    )
    return flags, size, envelope, raw

# Obsługa połączenia z jednym klientem
def handle_client(conn: socket.socket):
    def send(line: str):
        data = line + "\r\n"
        print(f"  S: {line}")
        conn.sendall(data.encode())

    def recv_line() -> str:
        buf = b""
        while True:
            ch = conn.recv(1)
            if not ch:
                return ""
            if ch == b"\n":
                return buf.decode(errors="replace").strip()
            if ch != b"\r":
                buf += ch

    state = "NOT_AUTHENTICATED"   # NOT_AUTHENTICATED | AUTHENTICATED | SELECTED | LOGOUT
    selected_mailbox = None

    # Powitanie
    send("* OK [CAPABILITY IMAP4rev1 LITERAL+ STARTTLS AUTH=PLAIN] SimIMAP ready")

    while True:
        raw = recv_line()
        if not raw:
            print("  [połączenie zamknięte przez klienta]")
            break

        print(f"  C: {raw}")
        parts = raw.split(None, 2)
        if len(parts) < 2:
            continue

        tag = parts[0]
        cmd = parts[1].upper()
        args = parts[2] if len(parts) > 2 else ""

        # CAPABILITY
        if cmd == "CAPABILITY":
            send("* CAPABILITY IMAP4rev1 LITERAL+")
            send(f"{tag} OK CAPABILITY completed")

        # NOOP 
        elif cmd == "NOOP":
            send(f"{tag} OK NOOP completed")

        # LOGOUT
        elif cmd == "LOGOUT":
            send("* BYE SimIMAP logging out")
            send(f"{tag} OK LOGOUT completed")
            state = "LOGOUT"
            break

        # LOGIN
        elif cmd == "LOGIN":
            creds = args.split(None, 1)
            user = creds[0].strip('"') if len(creds) > 0 else ""
            passwd = creds[1].strip('"') if len(creds) > 1 else ""
            if user == VALID_USER and passwd == VALID_PASS:
                state = "AUTHENTICATED"
                send(f"{tag} OK LOGIN completed")
            else:
                send(f"{tag} NO [AUTHENTICATIONFAILED] Invalid credentials")

        # AUTHENTICATE
        elif cmd == "AUTHENTICATE":
            send(f"{tag} NO AUTHENTICATE not supported, use LOGIN")

        # LIST 
        elif cmd == "LIST":
            if state == "NOT_AUTHENTICATED":
                send(f"{tag} NO Please login first")
                continue
            send('* LIST (\\HasNoChildren) "/" "INBOX"')
            send(f"{tag} OK LIST completed")

        # LSUB
        elif cmd == "LSUB":
            if state == "NOT_AUTHENTICATED":
                send(f"{tag} NO Please login first")
                continue
            send('* LSUB () "/" "INBOX"')
            send(f"{tag} OK LSUB completed")

        # SELECT
        elif cmd == "SELECT":
            if state == "NOT_AUTHENTICATED":
                send(f"{tag} NO Please login first")
                continue
            mailbox = args.strip().strip('"').upper()
            if mailbox == "INBOX":
                selected_mailbox = "INBOX"
                state = "SELECTED"
                n = len(MESSAGES)
                unseen = sum(1 for m in MESSAGES if not m["flags"])
                send(f"* {n} EXISTS")
                send("* 0 RECENT")
                send(f"* OK [UNSEEN {unseen}] First unseen message")
                send("* OK [UIDVALIDITY 1] UIDs valid")
                send(f"* OK [UIDNEXT {n+1}] Predicted next UID")
                send("* FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft)")
                send("* OK [PERMANENTFLAGS (\\Deleted \\Seen \\*)] Limited")
                send(f"{tag} OK [READ-WRITE] SELECT completed")
            else:
                send(f"{tag} NO No such mailbox")

        # EXAMINE
        elif cmd == "EXAMINE":
            if state == "NOT_AUTHENTICATED":
                send(f"{tag} NO Please login first")
                continue
            mailbox = args.strip().strip('"').upper()
            if mailbox == "INBOX":
                selected_mailbox = "INBOX"
                state = "SELECTED"
                n = len(MESSAGES)
                send(f"* {n} EXISTS")
                send("* 0 RECENT")
                send(f"* OK [UIDVALIDITY 1] UIDs valid")
                send(f"* OK [UIDNEXT {n+1}] Predicted next UID")
                send("* FLAGS (\\Answered \\Flagged \\Deleted \\Seen \\Draft)")
                send(f"{tag} OK [READ-ONLY] EXAMINE completed")
            else:
                send(f"{tag} NO No such mailbox")

        # STATUS
        elif cmd == "STATUS":
            if state == "NOT_AUTHENTICATED":
                send(f"{tag} NO Please login first")
                continue
            tokens = args.split(None, 1)
            mbox = tokens[0].strip('"').upper() if tokens else ""
            if mbox == "INBOX":
                n = len(MESSAGES)
                unseen = sum(1 for m in MESSAGES if not m["flags"])
                send(f"* STATUS INBOX (MESSAGES {n} UNSEEN {unseen} RECENT 0 UIDNEXT {n+1} UIDVALIDITY 1)")
                send(f"{tag} OK STATUS completed")
            else:
                send(f"{tag} NO No such mailbox")

        # FETCH
        elif cmd == "FETCH":
            if state != "SELECTED":
                send(f"{tag} NO No mailbox selected")
                continue

            # Parsuj zakres wiadomości i atrybuty
            fetch_parts = args.split(None, 1)
            seq_set = fetch_parts[0] if fetch_parts else ""
            attr_str = fetch_parts[1].upper() if len(fetch_parts) > 1 else ""

            # Rozwiąż sekwencję: n, n:m, n:*
            def resolve_seq(s: str, total: int):
                indices = set()
                for part in s.split(","):
                    part = part.strip()
                    if ":" in part:
                        lo, hi = part.split(":", 1)
                        lo = 1 if lo == "*" else int(lo)
                        hi = total if hi == "*" else int(hi)
                        for i in range(lo, hi + 1):
                            if 1 <= i <= total:
                                indices.add(i)
                    else:
                        v = total if part == "*" else int(part)
                        if 1 <= v <= total:
                            indices.add(v)
                return sorted(indices)

            indices = resolve_seq(seq_set, len(MESSAGES))

            want_envelope  = "ENVELOPE"  in attr_str
            want_flags     = "FLAGS"     in attr_str
            want_body      = "BODY"      in attr_str or "RFC822" in attr_str
            want_bodystruc = "BODYSTRUCTURE" in attr_str
            want_size      = "RFC822.SIZE" in attr_str
            want_uid       = "UID"       in attr_str

            # Uproszczony BODY[] / BODY[TEXT] / BODY[HEADER]
            want_body_full   = "BODY[]" in attr_str or "BODY.PEEK[]" in attr_str
            want_body_header = "BODY[HEADER]" in attr_str or "BODY.PEEK[HEADER]" in attr_str
            want_body_text   = "BODY[TEXT]" in attr_str or "BODY.PEEK[TEXT]" in attr_str

            for seq in indices:
                msg = MESSAGES[seq - 1]
                flags, size, envelope, raw = build_envelope(seq, msg)
                header_part = "\r\n".join(raw.split("\r\n\r\n")[0].split("\r\n")) + "\r\n\r\n"
                body_part   = msg["body"]

                resp_items = []

                if want_flags:
                    resp_items.append(f"FLAGS {flags}")
                if want_uid:
                    resp_items.append(f"UID {seq}")
                if want_size or want_body:
                    resp_items.append(f"RFC822.SIZE {size}")
                if want_envelope:
                    resp_items.append(f"ENVELOPE {envelope}")
                if want_bodystruc:
                    resp_items.append(
                        f'BODYSTRUCTURE ("TEXT" "PLAIN" ("CHARSET" "UTF-8") NIL NIL "7BIT" {size} {raw.count(chr(10))} NIL NIL NIL)'
                    )
                if want_body_full:
                    encoded = raw
                    resp_items.append(f"BODY[] {{{len(encoded.encode())}}}")
                    send(f"* {seq} FETCH ({' '.join(resp_items)}")
                    conn.sendall((encoded + "\r\n").encode())
                    send(")")
                    continue
                if want_body_header:
                    resp_items.append(f"BODY[HEADER] {{{len(header_part.encode())}}}")
                    send(f"* {seq} FETCH ({' '.join(resp_items)}")
                    conn.sendall((header_part + "\r\n").encode())
                    send(")")
                    continue
                if want_body_text:
                    resp_items.append(f"BODY[TEXT] {{{len(body_part.encode())}}}")
                    send(f"* {seq} FETCH ({' '.join(resp_items)}")
                    conn.sendall((body_part + "\r\n").encode())
                    send(")")
                    continue

                send(f"* {seq} FETCH ({' '.join(resp_items)})")

            send(f"{tag} OK FETCH completed")

        # STORE
        elif cmd == "STORE":
            if state != "SELECTED":
                send(f"{tag} NO No mailbox selected")
                continue
            # Symulacja: akceptujemy ale nic nie robimy
            send(f"{tag} OK STORE completed")

        # SEARCH
        elif cmd == "SEARCH":
            if state != "SELECTED":
                send(f"{tag} NO No mailbox selected")
                continue
            # Zwróć wszystkie numery sekwencyjne
            all_seqs = " ".join(str(i+1) for i in range(len(MESSAGES)))
            send(f"* SEARCH {all_seqs}")
            send(f"{tag} OK SEARCH completed")

        # EXPUNGE
        elif cmd == "EXPUNGE":
            if state != "SELECTED":
                send(f"{tag} NO No mailbox selected")
                continue
            send(f"{tag} OK EXPUNGE completed")

        # CLOSE
        elif cmd == "CLOSE":
            if state != "SELECTED":
                send(f"{tag} NO No mailbox selected")
                continue
            state = "AUTHENTICATED"
            selected_mailbox = None
            send(f"{tag} OK CLOSE completed")

        # ── UID (proxy do FETCH/SEARCH/STORE/COPY) ─
        elif cmd == "UID":
            if state != "SELECTED":
                send(f"{tag} NO No mailbox selected")
                continue
            sub_parts = args.split(None, 1)
            sub_cmd = sub_parts[0].upper() if sub_parts else ""
            sub_args = sub_parts[1] if len(sub_parts) > 1 else ""
            if sub_cmd in ("FETCH", "SEARCH", "STORE", "COPY"):
                # Dla uproszczenia traktujemy UID == numer sekwencyjny
                # (w symulacji UID = numer sekwencyjny)
                fake_raw = f"{tag} {sub_cmd} {sub_args}"
                # Re-dispatch rekurencyjnie przez fałszywy wiersz
                if sub_cmd == "FETCH":
                    fetch_parts = sub_args.split(None, 1)
                    seq_set = fetch_parts[0]
                    attr_str = (fetch_parts[1] if len(fetch_parts) > 1 else "").upper()

                    def resolve_seq(s, total):
                        indices = set()
                        for part in s.split(","):
                            part = part.strip()
                            if ":" in part:
                                lo, hi = part.split(":", 1)
                                lo = 1 if lo == "*" else int(lo)
                                hi = total if hi == "*" else int(hi)
                                for i in range(lo, hi + 1):
                                    if 1 <= i <= total:
                                        indices.add(i)
                            else:
                                v = total if part == "*" else int(part)
                                if 1 <= v <= total:
                                    indices.add(v)
                        return sorted(indices)

                    indices = resolve_seq(seq_set, len(MESSAGES))
                    for seq in indices:
                        msg = MESSAGES[seq - 1]
                        flags, size, envelope, raw = build_envelope(seq, msg)
                        if "BODY[]" in attr_str or "RFC822" in attr_str:
                            send(f"* {seq} FETCH (UID {seq} FLAGS {flags} RFC822.SIZE {size} BODY[] {{{len(raw.encode())}}})")
                            conn.sendall((raw + "\r\n").encode())
                            send(")")
                        elif "ENVELOPE" in attr_str:
                            send(f"* {seq} FETCH (UID {seq} FLAGS {flags} RFC822.SIZE {size} ENVELOPE {envelope})")
                        else:
                            send(f"* {seq} FETCH (UID {seq} FLAGS {flags} RFC822.SIZE {size})")
                    send(f"{tag} OK UID FETCH completed")
                elif sub_cmd == "SEARCH":
                    all_seqs = " ".join(str(i+1) for i in range(len(MESSAGES)))
                    send(f"* SEARCH {all_seqs}")
                    send(f"{tag} OK UID SEARCH completed")
                else:
                    send(f"{tag} OK UID {sub_cmd} completed")
            else:
                send(f"{tag} BAD Unknown UID subcommand: {sub_cmd}")

        # ── CREATE / DELETE / RENAME / SUBSCRIBE / UNSUBSCRIBE ─
        elif cmd in ("CREATE", "DELETE", "RENAME", "SUBSCRIBE", "UNSUBSCRIBE", "COPY", "APPEND"):
            send(f"{tag} NO {cmd} not supported by this server")

        # Nieznana komenda
        else:
            send(f"{tag} BAD Command '{cmd}' not recognized or not implemented")

    conn.close()
    print("  [połączenie zakończone]")


# Główna pętla serwera

def main():
    host = "127.0.0.1"
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 1143

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(1)
        print(f"[SimIMAP] Nasłuchuję na {host}:{port}")
        print(f"[SimIMAP] Login: {VALID_USER}  Hasło: {VALID_PASS}")
        print("[SimIMAP] Ctrl+C aby zatrzymać\n")

        while True:
            try:
                conn, addr = srv.accept()
                print(f"\n[SimIMAP] Nowe połączenie od {addr[0]}:{addr[1]}")
                try:
                    handle_client(conn)
                except Exception as e:
                    print(f"  [błąd obsługi klienta] {e}")
            except KeyboardInterrupt:
                print("\n[SimIMAP] Zatrzymuję serwer.")
                break


if __name__ == "__main__":
    main()