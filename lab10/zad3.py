"""
Napisz program klienta, który nawiąże połączenie (handshake) z serwerem obsługującym protokół WebSocket, 
działającym pod adresem ws://echo.websocket.org na porcie 80, a następnie, po nawiązaniu
połączenia, wyśle do niego wiadomość tekstową o dowolnej długości.
"""

import socket
import ssl
import base64
import os
import hashlib

# Konfiguracja
HOST = "echo.websocket.org"
PORT = 443
PATH = "/"


def generate_ws_key() -> str:
    # Generuje losowy 16-bajtowy klucz Base64 (RFC 6455).
    return base64.b64encode(os.urandom(16)).decode("utf-8")


def expected_accept(ws_key: str) -> str:
    """
    Oblicza oczekiwaną wartość Sec-WebSocket-Accept (RFC 6455, sekcja 4.2.2):
      SHA1(klucz + magiczny UUID) zakodowany Base64.
    """
    MAGIC    = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = (ws_key + MAGIC).encode("utf-8")
    return base64.b64encode(hashlib.sha1(combined).digest()).decode("utf-8")


def do_handshake(sock, host: str, path: str) -> bool:
    """
    Wysyła żądanie HTTP Upgrade i weryfikuje odpowiedź 101.
    Nagłówki wymagane przez RFC 6455:
      Upgrade: websocket, Connection: Upgrade,
      Sec-WebSocket-Key, Sec-WebSocket-Version: 13
    """
    ws_key = generate_ws_key()

    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {ws_key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"Origin: https://{host}\r\n"
        f"\r\n"
    )

    print("--- Wysyłany handshake ---")
    print(handshake)
    sock.sendall(handshake.encode("utf-8"))

    response = b""
    while b"\r\n\r\n" not in response:
        chunk = sock.recv(1024)
        if not chunk:
            break
        response += chunk

    response_text = response.decode("utf-8", errors="replace")
    print("--- Odpowiedź serwera ---")
    print(response_text)

    if "101" not in response_text:
        print("[-] Handshake nieudany – brak kodu 101")
        return False

    expected = expected_accept(ws_key)
    if expected not in response_text:
        print(f"[-] Nieprawidłowy Sec-WebSocket-Accept! Oczekiwano: {expected}")
        return False

    print("[+] Handshake zakończony sukcesem!\n")
    return True


def encode_frame(message: str) -> bytes:
    payload     = message.encode("utf-8")
    length      = len(payload)
    masking_key = os.urandom(4)   # RFC 6455: klient ZAWSZE maskuje

    # Bajt 0: FIN=1, opcode=1 (tekst)
    byte0 = 0x81

    # Bajt 1 + ewentualne bajty rozszerzonej długości
    if length <= 125:
        # Krótka wiadomość — długość mieści się w 7 bitach
        header = bytes([byte0, 0x80 | length])
    elif length <= 65535:
        # Średnia wiadomość — 2 dodatkowe bajty na długość
        header = bytes([byte0, 0x80 | 126]) + length.to_bytes(2, "big")
    else:
        # Długa wiadomość — 8 dodatkowych bajtów na długość
        header = bytes([byte0, 0x80 | 127]) + length.to_bytes(8, "big")

    # Maskowanie XOR — każdy bajt payloadu XOR odpowiedni bajt klucza (cyklicznie)
    masked_payload = bytes(payload[i] ^ masking_key[i % 4] for i in range(length))

    return header + masking_key + masked_payload


def decode_frame(sock) -> tuple[int, bytes]:
    """
    Odbiera i dekoduje ramkę WebSocket od serwera czytając z gniazda.
    Serwer NIE maskuje danych (RFC 6455, sekcja 5.1).
    Zwraca (opcode, payload).

    Czytamy bajt po bajcie nagłówek, potem payload — obsługuje dowolną długość.
    """
    def recv_exact(n: int) -> bytes:
        # Odbiera dokładnie n bajtów z gniazda.
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Połączenie zamknięte podczas odbioru")
            buf += chunk
        return buf

    # Bajt 0: FIN + opcode
    byte0  = recv_exact(1)[0]
    opcode = byte0 & 0x0F

    # Bajt 1: MASK + długość
    byte1  = recv_exact(1)[0]
    masked = (byte1 & 0x80) != 0
    length = byte1 & 0x7F

    # Rozszerzona długość
    if length == 126:
        length = int.from_bytes(recv_exact(2), "big")
    elif length == 127:
        length = int.from_bytes(recv_exact(8), "big")

    # Masking key (jeśli serwer maskuje — normalnie nie powinien)
    if masked:
        key     = recv_exact(4)
        payload = bytes(b ^ key[i % 4] for i, b in enumerate(recv_exact(length)))
    else:
        payload = recv_exact(length)

    return opcode, payload


def send_close(sock):
    # Wysyła ramkę Close (opcode 0x8) — poprawne zamknięcie WS (RFC 6455).
    sock.sendall(bytes([0x88, 0x80]) + os.urandom(4))
    print("[*] Wysłano ramkę Close")


def describe_frame_header(frame: bytes, payload_len: int):
    # Wypisuje czytelną interpretację nagłówka ramki WebSocket.
    print(f"    Bajt 0:  0x{frame[0]:02x}  → FIN=1, Opcode=0x1 (tekst)")
    if payload_len <= 125:
        print(f"    Bajt 1:  0x{frame[1]:02x}  → MASK=1, len={payload_len} (bezpośrednio)")
        mk_start = 2
    elif payload_len <= 65535:
        print(f"    Bajt 1:  0x{frame[1]:02x}  → MASK=1, len=126 (następne 2 bajty)")
        print(f"    Bajty 2-3: {frame[2:4].hex()} → długość={payload_len}")
        mk_start = 4
    else:
        print(f"    Bajt 1:  0x{frame[1]:02x}  → MASK=1, len=127 (następne 8 bajtów)")
        print(f"    Bajty 2-9: {frame[2:10].hex()} → długość={payload_len}")
        mk_start = 10
    print(f"    Masking key: {frame[mk_start:mk_start+4].hex()}")
    print(f"    Payload (zamaskowany, pierwsze 16 B): {frame[mk_start+4:mk_start+20].hex()}...")


def main():
    # Pobieramy wiadomość od użytkownika — może być dowolnej długości
    print("Podaj wiadomość do wysłania (Enter aby zatwierdzić):")
    message = input(">> ").strip()
    if not message:
        message = "A" * 200   # domyślna wiadomość >125 bajtów, żeby pokazać extended length

    msg_bytes = message.encode("utf-8")
    length    = len(msg_bytes)
    print(f"\n[*] Długość wiadomości: {length} bajtów", end="  →  ")

    # Informujemy, który wariant kodowania długości zostanie użyty
    if length <= 125:
        print("kodowanie 7-bitowe (1 bajt długości)")
    elif length <= 65535:
        print("kodowanie 16-bitowe (bajt 126 + 2 bajty długości)")
    else:
        print("kodowanie 64-bitowe (bajt 127 + 8 bajtów długości)")

    print(f"\n[*] Łączę z wss://{HOST}:{PORT} ...")
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.settimeout(10)
    raw_sock.connect((HOST, PORT))
    print(f"[+] Połączono TCP z {HOST}:{PORT}")

    # TLS — wymagane dla wss:// (port 443)
    ssl_context = ssl.create_default_context()
    sock = ssl_context.wrap_socket(raw_sock, server_hostname=HOST)
    print(f"[+] Nawiązano TLS, cipher: {sock.cipher()[0]}")

    try:
        # Krok 1: Handshake HTTP → WebSocket
        if not do_handshake(sock, HOST, PATH):
            return

        # Krok 2: Kodujemy i wysyłamy wiadomość dowolnej długości
        frame = encode_frame(message)
        sock.sendall(frame)
        print(f"[→] Wysłano ramkę ({len(frame)} bajtów łącznie):")
        describe_frame_header(frame, length)

        # Krok 3: Odbieramy odpowiedź serwera
        sock.settimeout(5)
        opcode, payload = decode_frame(sock)

        if opcode == 0x1:
            received = payload.decode("utf-8", errors="replace")
            # Skracamy wydruk dla bardzo długich wiadomości
            preview = received if len(received) <= 80 else received[:80] + f"... [{len(received)} znaków]"
            print(f"\n[←] Odebrano: {preview!r}")
            print("[+] Wymiana wiadomości WebSocket zakończona sukcesem ✓")
        elif opcode == 0x8:
            print("[*] Serwer zamknął połączenie przed odpowiedzią")
        else:
            print(f"[?] Nieoczekiwany opcode: 0x{opcode:02x}")

    finally:
        # Krok 4: Poprawne zamknięcie połączenia WebSocket
        send_close(sock)
        sock.close()


if __name__ == "__main__":
    main()