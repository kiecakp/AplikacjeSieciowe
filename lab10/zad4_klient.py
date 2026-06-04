import socket
import base64
import os
import hashlib

HOST = "127.0.0.1"
PORT = 9001
PATH = "/"


def generate_ws_key() -> str:
    return base64.b64encode(os.urandom(16)).decode("utf-8")


def expected_accept(ws_key: str) -> str:
    MAGIC    = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = (ws_key + MAGIC).encode("utf-8")
    return base64.b64encode(hashlib.sha1(combined).digest()).decode("utf-8")


def do_handshake(sock, host: str, path: str) -> bool:
    ws_key    = generate_ws_key()
    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{PORT}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {ws_key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"Origin: http://{host}\r\n"   # http:// — lokalny serwer bez TLS
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
    """
    Koduje wiadomość tekstową jako ramkę WebSocket — obsługuje dowolną długość.
    Klient ZAWSZE maskuje dane (RFC 6455).
    """
    payload     = message.encode("utf-8")
    length      = len(payload)
    masking_key = os.urandom(4)
    byte0       = 0x81  # FIN=1, opcode=tekst

    if length <= 125:
        header = bytes([byte0, 0x80 | length])
    elif length <= 65535:
        header = bytes([byte0, 0x80 | 126]) + length.to_bytes(2, "big")
    else:
        header = bytes([byte0, 0x80 | 127]) + length.to_bytes(8, "big")

    masked = bytes(payload[i] ^ masking_key[i % 4] for i in range(length))
    return header + masking_key + masked


def recv_exact(sock, n: int) -> bytes:
    """Odbiera dokładnie n bajtów z gniazda."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Połączenie zamknięte")
        buf += chunk
    return buf


def decode_frame(sock) -> tuple[int, bytes]:
    """
    Odbiera ramkę WebSocket od serwera.
    Serwer NIE maskuje (RFC 6455, sekcja 5.1).
    """
    opcode = recv_exact(sock, 1)[0] & 0x0F
    byte1  = recv_exact(sock, 1)[0]
    masked = (byte1 & 0x80) != 0
    length = byte1 & 0x7F

    if length == 126:
        length = int.from_bytes(recv_exact(sock, 2), "big")
    elif length == 127:
        length = int.from_bytes(recv_exact(sock, 8), "big")

    if masked:
        key     = recv_exact(sock, 4)
        payload = bytes(b ^ key[i % 4] for i, b in enumerate(recv_exact(sock, length)))
    else:
        payload = recv_exact(sock, length)

    return opcode, payload


def send_close(sock):
    """Wysyła ramkę Close — poprawne zamknięcie WS (RFC 6455)."""
    sock.sendall(bytes([0x88, 0x80]) + os.urandom(4))
    print("[*] Wysłano ramkę Close")


def main():
    print("Podaj wiadomość do wysłania (Enter aby zatwierdzić):")
    message = input(">> ").strip()
    if not message:
        message = "A" * 200   # domyślna wiadomość >125 bajtów

    msg_bytes = message.encode("utf-8")
    length    = len(msg_bytes)
    print(f"\n[*] Długość wiadomości: {length} bajtów", end="  →  ")
    if length <= 125:
        print("kodowanie 7-bitowe")
    elif length <= 65535:
        print("kodowanie 16-bitowe (extended 2B)")
    else:
        print("kodowanie 64-bitowe (extended 8B)")

    # Zwykłe gniazdo TCP — bez TLS (ws://, nie wss://)
    print(f"\n[*] Łączę z ws://{HOST}:{PORT} ...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((HOST, PORT))
    print(f"[+] Połączono TCP z {HOST}:{PORT}  (bez TLS)")

    try:
        if not do_handshake(sock, HOST, PATH):
            return

        frame = encode_frame(message)
        sock.sendall(frame)
        print(f"[→] Wysłano ramkę ({len(frame)} B): payload={length} B, "
              f"masking_key={frame[2:6].hex() if length<=125 else frame[4:8].hex()}")

        sock.settimeout(5)
        opcode, payload = decode_frame(sock)

        if opcode == 0x1:
            received = payload.decode("utf-8", errors="replace")
            preview  = received if len(received) <= 80 else received[:80] + f"... [{len(received)} zn.]"
            print(f"[←] Odebrano: {preview!r}")
            print("[+] Wymiana zakończona sukcesem ✓")
        elif opcode == 0x8:
            print("[*] Serwer zamknął połączenie")
        else:
            print(f"[?] Nieoczekiwany opcode: 0x{opcode:02x}")

    finally:
        send_close(sock)
        sock.close()


if __name__ == "__main__":
    main()