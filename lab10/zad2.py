"""
Napisz program klienta, który nawiąże połączenie (handshake) z serwerem obsługującym protokół WebSocket, 
działającym pod adresem ws://echo.websocket.org na porcie 80, a następnie, po nawiązaniu
połączenia, wyśle do niego krótką (nie dłuższą niż 125 bajtów) wiadomość tekstową.
"""

import socket
import ssl
import base64
import os
import hashlib

# Konfiguracja
HOST    = "echo.websocket.org"
PORT    = 443
PATH    = "/"
MESSAGE = "Witaj, WebSocket!"   # max 125 bajtów (krótka wiadomość)


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

    # Odbieramy odpowiedź aż do końca nagłówków HTTP
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
        print("[-] Handshake nieudany - brak kodu 101")
        return False

    expected = expected_accept(ws_key)
    if expected not in response_text:
        print(f"[-] Nieprawidłowy Sec-WebSocket-Accept! Oczekiwano: {expected}")
        return False

    print("[+] Handshake zakończony sukcesem!\n")
    return True


def encode_frame_text(message: str) -> bytes:
    """
    Koduje krótką wiadomość tekstową (≤ 125 B) jako ramkę WebSocket.

    Struktura ramki dla krótkiej wiadomości:
      Bajt 0: 0x81  →  FIN=1, RSV=000, Opcode=0001 (tekst)
      Bajt 1: 0x80 | len  →  MASK=1, długość w 1 bajcie (≤ 125)
      Bajty 2-5: masking key (4 losowe bajty)
      Bajty 6+:  payload XOR masking key

    RFC 6455: klient ZAWSZE musi maskować dane wysyłane do serwera.
    """
    payload = message.encode("utf-8")
    assert len(payload) <= 125, "Ta funkcja obsługuje tylko wiadomości ≤ 125 bajtów"

    masking_key = os.urandom(4)
    masked      = bytes(payload[i] ^ masking_key[i % 4] for i in range(len(payload)))

    return bytes([0x81, 0x80 | len(payload)]) + masking_key + masked


def decode_frame(data: bytes) -> tuple[int, bytes]:
    """
    Dekoduje ramkę WebSocket od serwera.
    Serwer NIE maskuje — RFC 6455 sekcja 5.1.
    Zwraca (opcode, payload).
    """
    if len(data) < 2:
        return 0, b""

    opcode = data[0] & 0x0F
    masked = (data[1] & 0x80) != 0
    length = data[1] & 0x7F
    offset = 2

    if length == 126:
        length = int.from_bytes(data[2:4], "big")
        offset = 4
    elif length == 127:
        length = int.from_bytes(data[2:10], "big")
        offset = 10

    if masked:
        key     = data[offset:offset + 4]
        offset += 4
        payload = bytes(data[offset + i] ^ key[i % 4] for i in range(length))
    else:
        payload = data[offset:offset + length]

    return opcode, payload


def send_close(sock):
    # Wysyła ramkę Close (opcode 0x8) — poprawne zamknięcie WS (RFC 6455).
    sock.sendall(bytes([0x88, 0x80]) + os.urandom(4))
    print("[*] Wysłano ramkę Close")


def main():
    msg_bytes = MESSAGE.encode("utf-8")
    print(f"[*] Wiadomość do wysłania: {MESSAGE!r} ({len(msg_bytes)} bajtów)")

    print(f"[*] Łączę z wss://{HOST}:{PORT} ...")
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

        # Krok 2: Wysyłamy krótką wiadomość tekstową (≤ 125 bajtów)
        # Ramka: 2 bajty nagłówka + 4 bajty masking key + payload
        frame = encode_frame_text(MESSAGE)
        sock.sendall(frame)
        print(f"[→] Wysłano ramkę ({len(frame)} bajtów łącznie):")
        print(f"    Nagłówek:     {frame[:2].hex()}  "
              f"(0x81=tekst/FIN, 0x{frame[1]:02x}=MASK+len={len(msg_bytes)})")
        print(f"    Masking key:  {frame[2:6].hex()}")
        print(f"    Payload mask: {frame[6:].hex()}")

        # Krok 3: Odbieramy odpowiedź serwera
        sock.settimeout(5)
        data = b""
        while len(data) < 2:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk

        opcode, payload = decode_frame(data)

        if opcode == 0x1:
            received = payload.decode("utf-8", errors="replace")
            print(f"\n[←] Odebrano: {received!r}")
            print("[+] Wymiana wiadomości WebSocket zakończona sukcesem ✓")
        elif opcode == 0x8:
            print("[*] Serwer zamknął połączenie przed odpowiedzią")
        else:
            print(f"[?] Nieoczekiwany opcode: 0x{opcode:02x}, payload: {payload.hex()}")

    finally:
        # Krok 4: Poprawne zamknięcie połączenia WebSocket
        send_close(sock)
        sock.close()


if __name__ == "__main__":
    main()