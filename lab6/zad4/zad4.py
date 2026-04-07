"""
Wykorzystując protokół telnet, oraz serwer ESMTP działający pod adresem 
interia.pl na porcie 587 wyślij wiadomość e-mail używając komend protokołu 
ESMTP. Do wiadomości dodaj załącznik - dowolny plik tekstowy (sprawdź format 
MIME: Multipart i Content-Type). Możesz wykorzystać openssl do przekonwertowania 
pliku: cat plik |openssl base64.
"""

import socket
import ssl
import base64

HOST = 'poczta.interia.pl'
PORT = 587

LOGIN = 'pas2026inf@interia.pl'
PASSWORD = 'Piii4SInf2026'
NADAWCA = 'pas2026inf@interia.pl'
ODBIORCA = 'pasinf2026@interia.pl'
TEMAT = 'Zadanie 4 - Email z zalacznikiem'
WIADOMOSC = 'To jest testowa wiadomość e-mail wysłana za pomocą protokołu ESMTP.'

boundary = 'BOUNDARY123'
encoded_file = 'VG8gamVzdCBwbGlrIGRvIHphZGFuaWEgNCA6Mw=='   # przykładowa zawartość pliku zakodowana w Base64 (tekst "To jest plik do zadania 4 :3")

def b64(text: str) -> str:
    # koduje tekst do Base64 (wymagane przez AUTH LOGIN)
    return base64.b64encode(text.encode()).decode()

def send_command(sock: socket.socket, command: str, expected_code: int = None) -> str:
    # wysyla komende do serwera i odbiera odpowiedz
    print(f'>>> {command}')
    sock.sendall((command + '\r\n').encode())
    response = get_response(sock)

    if expected_code and not response.startswith(str(expected_code)):
        raise Exception(f'Expected response code {expected_code}, but got: {response}')
    return response

def get_response(sock: socket.socket) -> str:
    # odbiera odpowiedz od serwera (moze byc wieloczesciowa)
    response = b''
    while True:
        chunk = sock.recv(4096)
        response += chunk

        # odpowiedz SMTP jest kompletna gdy linia ma format: KOD<spacja>tekst\r\n
        # (wieloliniowe odpowiedz uzywaja KOD-tekst\r\n)
        line = response.decode(errors='replace').splitlines()
        if line and len(line[-1]) >= 4 and line[-1][3] == ' ':
            break

        if not chunk:
            break
    
    response_str = response.decode(errors='replace').strip()
    print(f'<<< {response_str}')
    return response_str

def main():
    print(f"Connecting to {HOST}:{PORT}...")
    sock = socket.create_connection((HOST, PORT), timeout=5)

    try:
        # Odbierz powitanie serwera
        get_response(sock)

        # Wyslij EHLO
        send_command(sock, f'EHLO {socket.gethostname()}', expected_code=250)

        # STARTTLS - rozpoczecie bezpiecznej sesji TLS
        send_command(sock, 'STARTTLS', expected_code=220)

        # Owijamy socket w TLS
        context = ssl.create_default_context()
        tls_sock = context.wrap_socket(sock, server_hostname=HOST)
        print("   TLS connection established.")

        # EHLO ponownie po STARTTLS
        send_command(tls_sock, f'EHLO {socket.gethostname()}', expected_code=250)

        # AUTH LOGIN - uwierzytelnianie
        auth_string = '\0' + LOGIN + '\0' + PASSWORD
        send_command(tls_sock, 'AUTH PLAIN ' + b64(auth_string), expected_code=235)

        # MAIL FROM - adres nadawcy
        send_command(tls_sock, f'MAIL FROM:<{NADAWCA}>', expected_code=250)

        # RCPT TO - adres odbiorcy
        send_command(tls_sock, f'RCPT TO:<{ODBIORCA}>', expected_code=250)

        # DATA - rozpoczecie tresci wiadomosci
        send_command(tls_sock, 'DATA', expected_code=354)

        # Tresc wiadomosci (naglowki + body)
        message = (
            f"From: {LOGIN}\r\n"
            f"To: <{ODBIORCA}>\r\n"
            f"Subject: {TEMAT}\r\n"
            f"MIME-Version: 1.0\r\n"
            f"Content-Type: multipart/mixed; boundary={boundary}\r\n"
            f"\r\n"

            f"--{boundary}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n"
            f"\r\n"
            f"{WIADOMOSC}\r\n"

            f"--{boundary}\r\n"
            f"Content-Type: text/plain; name=\"plik.txt\"\r\n"
            f"Content-Transfer-Encoding: base64\r\n"
            f"Content-Disposition: attachment; filename=\"plik.txt\"\r\n"
            f"\r\n"
            f"{encoded_file}\r\n"

            f"--{boundary}--\r\n"
            f".\r\n"
        )
        print(f'>>> [message body]')
        tls_sock.sendall(message.encode())
        response = get_response(tls_sock)
        if not response.startswith("250"):
            raise Exception(f"Email not accepted: {response}")

        # QUIT - zakonczenie sesji
        send_command(tls_sock, 'QUIT', expected_code=221)

        print("Email sent successfully!")

    except RuntimeError as e:
        print(f"Error: {e}")
    finally:
        tls_sock.close()

if __name__ == "__main__":
    main()