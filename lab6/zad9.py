"""
Napisz program klienta, który połączy się z serwerem ESMTP działającym 
pod adresem interia.pl na porcie 587, a następnie wyśle wiadomość e-mail 
używając komend protokołu ESMTP. Treść wiadomości powinna zostać sformatowana 
za pomocą tagów HTML, przykładowo: <b>pogrubienie</b>, <i>pochylenie</i>, 
<u>podkreślenie</u> i innych wybranych.

Do wykonania zadań możesz wykorzystać konta pocztowe:
    • pas2026inf@interia.pl z hasłem Piii4SInf2026
    • pasinf2026@interia.pl z hasłem Piii4SInf2026
"""

import socket
import ssl
import base64

HOST = 'poczta.interia.pl'
PORT = 587

# Dane do zalogowania
LOGIN = 'pas2026inf@interia.pl'
PASSWORD = 'Piii4SInf2026'

# Nadawca i odbiorca
NADAWCA = 'pas2026inf@interia.pl'
ODBIORCA = 'pasinf2026@interia.pl'

# Temat i treść HTML
TEMAT = 'Test HTML Email'
WIADOMOSC = """
<p>Wiadomość testowa HTML:</p>
<ul>
<li><b>Pogrubienie</b></li>
<li><i>Pochylenie</i></li>
<li><u>Podkreślenie</u></li>
<li>Prosty <span style="color:blue;">kolorowy tekst</span></li>
</ul>
"""

def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()

def send_command(sock: socket.socket, command: str, expected_code: int = None) -> str:
    print(f'>>> {command}')
    sock.sendall((command + '\r\n').encode())
    response = get_response(sock)
    if expected_code and not response.startswith(str(expected_code)):
        raise Exception(f'Expected {expected_code}, got: {response}')
    return response

def get_response(sock: socket.socket) -> str:
    response = b''
    while True:
        chunk = sock.recv(4096)
        response += chunk
        lines = response.decode(errors='replace').splitlines()
        if lines and len(lines[-1]) >= 4 and lines[-1][3] == ' ':
            break
        if not chunk:
            break
    response_str = response.decode(errors='replace').strip()
    print(f'<<< {response_str}')
    return response_str

def main():
    sock = socket.create_connection((HOST, PORT), timeout=5)
    try:
        get_response(sock)
        send_command(sock, f'EHLO {socket.gethostname()}', 250)
        send_command(sock, 'STARTTLS', 220)

        context = ssl.create_default_context()
        tls_sock = context.wrap_socket(sock, server_hostname=HOST)

        send_command(tls_sock, f'EHLO {socket.gethostname()}', 250)
        auth_string = '\0' + LOGIN + '\0' + PASSWORD
        send_command(tls_sock, 'AUTH PLAIN ' + b64(auth_string), 235)

        send_command(tls_sock, f'MAIL FROM:<{NADAWCA}>', 250)
        send_command(tls_sock, f'RCPT TO:<{ODBIORCA}>', 250)

        send_command(tls_sock, 'DATA', 354)

        message = (
            f"From: <{NADAWCA}>\r\n"
            f"To: <{ODBIORCA}>\r\n"
            f"Subject: {TEMAT}\r\n"
            f"MIME-Version: 1.0\r\n"
            f"Content-Type: text/html; charset=utf-8\r\n"
            f"\r\n"
            f"{WIADOMOSC}\r\n"
            f".\r\n"
        )

        print(">>> [wysyłanie wiadomości HTML]")
        tls_sock.sendall(message.encode())
        response = get_response(tls_sock)
        if not response.startswith("250"):
            raise Exception(f"Email not accepted: {response}")

        send_command(tls_sock, 'QUIT', 221)
        print("Email HTML wysłany pomyślnie!")

    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        try:
            tls_sock.close()
        except:
            sock.close()

if __name__ == "__main__":
    main()