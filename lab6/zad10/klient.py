"""
Kod klienta do testowania zad 10
"""

import socket
import base64

HOST = '127.0.0.1'
PORT = 1025  # port, na którym działa mock SMTP

LOGIN = 'pas2026inf@interia.pl'
PASSWORD = 'Piii4SInf2026'

NADAWCA = LOGIN
ODBIORCA = 'pasinf2026@interia.pl'
TEMAT = 'Test lokalny serwera SMTP'
WIADOMOSC = 'To jest testowa wiadomość wysłana do lokalnego serwera SMTP (symulacja).'

def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()

def send_command(sock, command, expected_code=None):
    print(f'>>> {command}')
    sock.sendall((command + '\r\n').encode())
    response = get_response(sock)
    if expected_code and not response.startswith(str(expected_code)):
        print(f"⚠️ Otrzymano inny kod niż oczekiwano: {response}")
    return response

def get_response(sock):
    """Odbiera odpowiedź SMTP, obsługuje wieloliniowe odpowiedzi."""
    response = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
        lines = response.decode().splitlines()
        # wieloliniowa odpowiedź kończy się, gdy linia zaczyna się kodem + spacja
        if lines and len(lines[-1]) >= 4 and lines[-1][3] == ' ':
            break
    print(f'<<< {response.decode().strip()}')
    return response.decode()

def main():
    print(f"[+] Łączenie z {HOST}:{PORT}...")
    sock = socket.create_connection((HOST, PORT))

    try:
        get_response(sock)  # powitanie serwera

        send_command(sock, f'EHLO klient', 250)

        # AUTH PLAIN (mock serwer zwraca zawsze 235)
        auth_str = '\0' + LOGIN + '\0' + PASSWORD
        send_command(sock, 'AUTH PLAIN ' + b64(auth_str), 235)

        send_command(sock, f'MAIL FROM:<{NADAWCA}>', 250)
        send_command(sock, f'RCPT TO:<{ODBIORCA}>', 250)

        send_command(sock, 'DATA', 354)

        # treść wiadomości
        message = (
            f"From: <{NADAWCA}>\r\n"
            f"To: <{ODBIORCA}>\r\n"
            f"Subject: {TEMAT}\r\n"
            f"\r\n"
            f"{WIADOMOSC}\r\n"
            f".\r\n"
        )

        print(">>> [wysyłanie wiadomości]")
        sock.sendall(message.encode())
        get_response(sock)  # odbierz 250 OK od serwera

        send_command(sock, 'QUIT', 221)
        print("✅ Test lokalnego serwera SMTP zakończony pomyślnie!")

    finally:
        sock.close()

if __name__ == "__main__":
    main()