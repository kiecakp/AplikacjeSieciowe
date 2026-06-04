"""
W poniższych zadaniach zakładamy, iż serwer powinien obsługiwać tylko jednego klienta w danej chwili.
Pod adresem ws://echo.websocket.org na porcie 80 (wersja niezabezpieczona) oraz
wss://echo.websocket.org, port 443 (wersja zabezpieczona) udostępniony jest serwer obsługujący protokół WebSocket.
Udostępniony jest też web client, do przetestowania serwera, w wersji niezabezpieczonej i zabezpieczonej,
odpowiednio http://websocket.org/echo.html oraz https://websocket.org/echo.html.

Napisz program klienta, który nawiąże połączenie (handshake) z serwerem obsługującym protokół WebSocket, 
działającym pod adresem ws://echo.websocket.org na porcie 80.
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
    """
    Generuje losowy 16-bajtowy klucz i koduje go Base64.
    Wymagane przez RFC 6455 — każde połączenie musi mieć unikalny klucz.
    """
    return base64.b64encode(os.urandom(16)).decode("utf-8")


def expected_accept(ws_key: str) -> str:
    """
    Oblicza oczekiwaną wartość Sec-WebSocket-Accept.
    Algorytm (RFC 6455, sekcja 4.2.2):
      1. Sklej klucz klienta z magicznym UUID
      2. Oblicz SHA-1
      3. Zakoduj Base64
    """
    MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined = (ws_key + MAGIC).encode("utf-8")
    return base64.b64encode(hashlib.sha1(combined).digest()).decode("utf-8")


def do_handshake(sock, host: str, path: str) -> bool:
    """
    Wysyła żądanie HTTP Upgrade i weryfikuje odpowiedź serwera.
    Zwraca True jeśli handshake się powiódł.

    Nagłówki wymagane przez RFC 6455:
      - Upgrade: websocket          — żądamy przełączenia protokołu
      - Connection: Upgrade         — informujemy, że to żądanie upgrade'u
      - Sec-WebSocket-Key           — losowy klucz Base64 (16 bajtów)
      - Sec-WebSocket-Version: 13   — jedyna wspierana wersja
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

    print("--- Wysyłany handshake HTTP ---")
    print(handshake)

    sock.sendall(handshake.encode("utf-8"))

    # Odbieramy odpowiedź serwera aż do końca nagłówków
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

    # Weryfikacja Sec-WebSocket-Accept — RFC 6455 wymaga sprawdzenia tego pola
    expected = expected_accept(ws_key)
    if expected not in response_text:
        print(f"[-] Nieprawidłowy Sec-WebSocket-Accept! Oczekiwano: {expected}")
        return False

    print("[+] Handshake WebSocket zakończony sukcesem!")
    return True


def encode_frame(message: str) -> bytes:
    """
    Koduje wiadomość tekstową jako ramkę WebSocket.

    Struktura ramki (RFC 6455, sekcja 5.2):
      Bajt 0: FIN(1) + RSV(3) + Opcode(4)
      Bajt 1: MASK(1) + Payload len(7)
      [N]:    Masking key (4 bajty) — WYMAGANE dla klienta
      [N+4]:  Payload XOR masking key
    """
    payload     = message.encode("utf-8")
    length      = len(payload)
    byte0       = 0x81              # FIN=1, opcode=1 (tekst)
    masking_key = os.urandom(4)     # RFC 6455: klient ZAWSZE maskuje

    if length <= 125:
        header = bytes([byte0, 0x80 | length])
    elif length <= 65535:
        header = bytes([byte0, 0x80 | 126]) + length.to_bytes(2, "big")
    else:
        header = bytes([byte0, 0x80 | 127]) + length.to_bytes(8, "big")

    # Maskowanie XOR — każdy bajt payloadu XOR odpowiedni bajt klucza (cyklicznie)
    masked_payload = bytes(payload[i] ^ masking_key[i % 4] for i in range(length))
    return header + masking_key + masked_payload


def decode_frame(data: bytes) -> tuple[int, bytes]:
    """
    Dekoduje ramkę WebSocket odebraną od serwera.
    Serwer NIE maskuje danych (RFC 6455: tylko klient maskuje).
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


def send_message(sock, message: str):
    # Wysyła wiadomość tekstową jako zamaskowaną ramkę WebSocket.
    sock.sendall(encode_frame(message))
    print(f"[→] Wysłano: {message!r}")


def receive_message(sock) -> str | None:
    # Odbiera ramkę WebSocket i zwraca jej treść tekstową.
    data = b""
    while len(data) < 2:
        chunk = sock.recv(4096)
        if not chunk:
            return None
        data += chunk

    opcode, payload = decode_frame(data)

    if opcode == 0x8:
        print("[*] Serwer zamknął połączenie (opcode Close)")
        return None
    if opcode == 0x1:
        return payload.decode("utf-8", errors="replace")
    if opcode == 0x2:
        return f"<dane binarne: {len(payload)} bajtów>"
    return None


def send_close(sock):
    """
    Wysyła ramkę Close (opcode 0x8) — poprawne zamknięcie WS.
    RFC 6455: obie strony muszą wysłać i odebrać ramkę Close.
    """
    masking_key = os.urandom(4)
    sock.sendall(bytes([0x88, 0x80]) + masking_key)
    print("[*] Wysłano ramkę Close")


def main():
    print(f"[*] Łączę z wss://{HOST}:{PORT} ...")

    # Tworzymy zwykłe gniazdo TCP
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.settimeout(10)
    raw_sock.connect((HOST, PORT))
    print(f"[+] Połączono TCP z {HOST}:{PORT}")

    # Opakowujemy gniazdo w TLS — WYMAGANE dla wss://
    # Bez tego serwer natychmiast resetuje połączenie (ConnectionResetError)
    ssl_context = ssl.create_default_context()
    sock = ssl_context.wrap_socket(raw_sock, server_hostname=HOST)
    print(f"[+] Nawiązano TLS, cipher: {sock.cipher()[0]}")

    try:
        # Krok 1: HTTP Upgrade → WebSocket (przez zaszyfrowany kanał TLS)
        if not do_handshake(sock, HOST, PATH):
            return

        # Krok 2: Pętla wysyłania wiadomości (echo test)
        print("\nWpisz wiadomość (lub 'quit' aby zakończyć):")
        sock.settimeout(5)

        while True:
            try:
                msg = input(">> ").strip()
            except EOFError:
                break

            if msg.lower() == "quit":
                break
            if not msg:
                continue

            send_message(sock, msg)

            # Serwer echo powinien odesłać tę samą wiadomość
            reply = receive_message(sock)
            if reply is not None:
                print(f"[←] Odebrano: {reply!r}")
            else:
                print("[-] Brak odpowiedzi lub połączenie zamknięte")
                break

    finally:
        # Krok 3: Poprawne zamknięcie połączenia WebSocket
        send_close(sock)
        sock.close()


if __name__ == "__main__":
    main()