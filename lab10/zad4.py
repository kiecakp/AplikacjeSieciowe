"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na określonym porcie TCP będzie
obsługiwał protokół WebSocket. Możesz ograniczyć się do wysyłania/odbierania danych w postaci tekstowej.
"""

import socket
import ssl
import base64
import hashlib
import os

# Konfiguracja
HOST = "127.0.0.1"
PORT = 9001


# ---------- Handshake ----------

def compute_accept(ws_key: str) -> str:
    """
    Oblicza wartość Sec-WebSocket-Accept (RFC 6455, sekcja 4.2.2):
      SHA1(klucz_klienta + magiczny UUID) zakodowany Base64.
    """
    MAGIC    = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = (ws_key + MAGIC).encode("utf-8")
    return base64.b64encode(hashlib.sha1(combined).digest()).decode("utf-8")


def do_handshake(sock: socket.socket) -> bool:
    """
    Odbiera żądanie HTTP Upgrade od klienta i odsyła odpowiedź 101.
    Zwraca True jeśli handshake się powiódł.
    """
    # Odbieramy żądanie HTTP aż do pustej linii (koniec nagłówków)
    raw = b""
    while b"\r\n\r\n" not in raw:
        chunk = sock.recv(1024)
        if not chunk:
            return False
        raw += chunk

    request = raw.decode("utf-8", errors="replace")
    print("--- Odebrane żądanie handshake ---")
    print(request)

    # Szukamy nagłówka Sec-WebSocket-Key — wymagany do obliczenia Accept
    ws_key = None
    for line in request.splitlines():
        if line.lower().startswith("sec-websocket-key:"):
            ws_key = line.split(":", 1)[1].strip()
            break

    if not ws_key:
        print("[-] Brak nagłówka Sec-WebSocket-Key — odrzucam połączenie")
        sock.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
        return False

    # Sprawdzamy czy klient żąda protokołu WebSocket
    if "upgrade: websocket" not in request.lower():
        print("[-] Brak nagłówka Upgrade: websocket — odrzucam połączenie")
        sock.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
        return False

    # Budujemy odpowiedź 101 Switching Protocols
    accept = compute_accept(ws_key)
    response = (
        f"HTTP/1.1 101 Switching Protocols\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        f"\r\n"
    )

    print("--- Wysyłana odpowiedź handshake ---")
    print(response)
    sock.sendall(response.encode("utf-8"))
    print("[+] Handshake zakończony sukcesem!\n")
    return True


# ---------- Ramki WebSocket ----------

def recv_exact(sock: socket.socket, n: int) -> bytes:
    """Odbiera dokładnie n bajtów z gniazda."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Połączenie zamknięte podczas odbioru")
        buf += chunk
    return buf


def decode_frame(sock: socket.socket) -> tuple[int, bytes]:
    """
    Odbiera i dekoduje ramkę WebSocket od klienta.
    Klient ZAWSZE maskuje dane (RFC 6455, sekcja 5.1) — demaskujemy XOR.
    Zwraca (opcode, payload).

    Opcody:
      0x1 = tekst
      0x2 = binarny
      0x8 = Close
      0x9 = Ping
      0xA = Pong
    """
    # Bajt 0: FIN + opcode
    byte0  = recv_exact(sock, 1)[0]
    opcode = byte0 & 0x0F

    # Bajt 1: MASK + długość bazowa
    byte1  = recv_exact(sock, 1)[0]
    masked = (byte1 & 0x80) != 0
    length = byte1 & 0x7F

    # Rozszerzona długość (RFC 6455, sekcja 5.2)
    if length == 126:
        # Następne 2 bajty to rzeczywista długość (big-endian)
        length = int.from_bytes(recv_exact(sock, 2), "big")
    elif length == 127:
        # Następne 8 bajtów to rzeczywista długość (big-endian)
        length = int.from_bytes(recv_exact(sock, 8), "big")

    # Masking key — 4 bajty, zawsze obecne gdy MASK=1
    if masked:
        key     = recv_exact(sock, 4)
        payload = bytes(b ^ key[i % 4] for i, b in enumerate(recv_exact(sock, length)))
    else:
        # Klient bez maski — naruszenie RFC, ale obsługujemy
        payload = recv_exact(sock, length)

    return opcode, payload


def encode_frame(message: str) -> bytes:
    """
    Koduje wiadomość tekstową jako ramkę WebSocket.
    Serwer NIE maskuje danych (RFC 6455: tylko klient maskuje).

    Bajt 0: 0x81 → FIN=1, Opcode=0x1 (tekst)
    Bajt 1: długość (bez bitu MASK — serwer nie maskuje)
    """
    payload = message.encode("utf-8")
    length  = len(payload)

    byte0 = 0x81  # FIN=1, opcode=tekst

    # Serwer nie ustawia bitu MASK (0x80) — brak masking key
    if length <= 125:
        header = bytes([byte0, length])
    elif length <= 65535:
        header = bytes([byte0, 126]) + length.to_bytes(2, "big")
    else:
        header = bytes([byte0, 127]) + length.to_bytes(8, "big")

    return header + payload


def send_frame_raw(sock: socket.socket, opcode: int, payload: bytes = b""):
    """
    Wysyła surową ramkę WebSocket z podanym opcodem (np. Close, Pong).
    Serwer nie maskuje.
    """
    length = len(payload)
    if length <= 125:
        header = bytes([0x80 | opcode, length])
    elif length <= 65535:
        header = bytes([0x80 | opcode, 126]) + length.to_bytes(2, "big")
    else:
        header = bytes([0x80 | opcode, 127]) + length.to_bytes(8, "big")
    sock.sendall(header + payload)


# ---------- Obsługa klienta ----------

def handle_client(conn: socket.socket, addr: tuple):
    """
    Obsługuje pojedyncze połączenie WebSocket:
      - handshake HTTP → WS
      - pętla odbioru/wysyłki ramek
      - obsługa Ping/Pong i Close
    """
    print(f"\n[+] Nowe połączenie od {addr[0]}:{addr[1]}")

    try:
        if not do_handshake(conn):
            return

        print(f"[*] Czekam na wiadomości od {addr[0]}:{addr[1]} ...")

        while True:
            opcode, payload = decode_frame(conn)

            if opcode == 0x1:
                # Ramka tekstowa — wyświetlamy i odsyłamy echo
                message = payload.decode("utf-8", errors="replace")
                print(f"[←] Odebrano tekst od {addr[0]}:{addr[1]}: {message!r}")

                # Echo — odsyłamy tę samą wiadomość z powrotem
                response = f"[ECHO] {message}"
                conn.sendall(encode_frame(response))
                print(f"[→] Wysłano echo: {response!r}")

            elif opcode == 0x2:
                # Ramka binarna — informujemy i ignorujemy
                print(f"[←] Odebrano dane binarne ({len(payload)} B) — ignoruję")

            elif opcode == 0x9:
                # Ping — odpowiadamy Pong z tym samym payloadem (RFC 6455)
                print(f"[←] Ping od {addr[0]}:{addr[1]} — odpowiadam Pong")
                send_frame_raw(conn, 0xA, payload)

            elif opcode == 0xA:
                # Pong — potwierdzenie naszego Pinga (logujemy)
                print(f"[←] Pong od {addr[0]}:{addr[1]}")

            elif opcode == 0x8:
                # Close — odsyłamy ramkę Close i kończymy połączenie
                print(f"[←] Close od {addr[0]}:{addr[1]} — zamykam połączenie")
                send_frame_raw(conn, 0x8, payload)  # echo kodu zamknięcia
                break

            else:
                print(f"[?] Nieznany opcode: 0x{opcode:02x} — ignoruję")

    except ConnectionError as e:
        print(f"[!] Połączenie zerwane przez {addr[0]}:{addr[1]}: {e}")
    except Exception as e:
        print(f"[!] Błąd obsługi {addr[0]}:{addr[1]}: {e}")
    finally:
        conn.close()
        print(f"[-] Rozłączono {addr[0]}:{addr[1]}")


# ---------- Główna pętla serwera ----------

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        # SO_REUSEADDR — pozwala od razu ponownie uruchomić serwer
        # bez czekania na wygaśnięcie TIME_WAIT
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT))
        # Zgodnie z treścią zadania: obsługujemy jednego klienta na raz
        server_sock.listen(1)
        print(f"[+] Serwer WebSocket nasłuchuje na ws://{HOST}:{PORT}/")
        print(f"[+] Ctrl+C aby zatrzymać\n")

        while True:
            conn, addr = server_sock.accept()
            # Jeden klient na raz — obsługujemy synchronicznie (bez wątków)
            handle_client(conn, addr)


if __name__ == "__main__":
    run_server()