"""
Napisz program klienta, który połączy się z serwerem ESMTP działającym 
pod adresem interia.pl na porcie 587, a następnie wyśle wiadomość e-mail 
używając komend protokołu ESMTP. Do wiadomości dodaj załącznik - dowolny 
plik tekstowy (sprawdź format MIME: Multipart i Content-Type). Nie wykorzystuj 
gotowych bibliotek. O adres nadawcy, odbiorcy (odbiorców), temat wiadomości i 
jej treść zapytaj użytkownika.

Do wykonania zadań możesz wykorzystać konta pocztowe:
    • pas2026inf@interia.pl z hasłem Piii4SInf2026
    • pasinf2026@interia.pl z hasłem Piii4SInf2026
"""

import socket
import ssl
import base64

HOST = 'poczta.interia.pl'
PORT = 587

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

def load_file_base64(filename: str) -> str:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    return base64.b64encode(content.encode()).decode()

def main():
    print("=== Klient ESMTP z załącznikiem ===")

    LOGIN = input("Podaj login (email): ")
    PASSWORD = input("Podaj hasło: ")

    NADAWCA = LOGIN
    odbiorcy_input = input("Podaj odbiorców (oddziel przecinkami): ")
    ODBIORCY = [o.strip() for o in odbiorcy_input.split(",")]

    TEMAT = input("Podaj temat: ")
    WIADOMOSC = input("Podaj treść wiadomości: ")

    plik_path = input("Podaj ścieżkę do pliku tekstowego, który ma być załącznikiem: ")
    encoded_file = load_file_base64(plik_path)

    boundary = "BOUNDARY123"

    message = (
        f"From: <{NADAWCA}>\r\n"
        f"To: {', '.join(ODBIORCY)}\r\n"
        f"Subject: {TEMAT}\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: multipart/mixed; boundary={boundary}\r\n"
        f"\r\n"

        # treść maila
        f"--{boundary}\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"\r\n"
        f"{WIADOMOSC}\r\n"

        # załącznik
        f"--{boundary}\r\n"
        f"Content-Type: text/plain; name=\"{plik_path.split('/')[-1]}\"\r\n"
        f"Content-Transfer-Encoding: base64\r\n"
        f"Content-Disposition: attachment; filename=\"{plik_path.split('/')[-1]}\"\r\n"
        f"\r\n"
        f"{encoded_file}\r\n"
        f"--{boundary}--\r\n"
        f".\r\n"
    )

    # połączenie z serwerem
    print(f"\nConnecting to {HOST}:{PORT}...")
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
        for odbiorca in ODBIORCY:
            send_command(tls_sock, f'RCPT TO:<{odbiorca}>', 250)

        send_command(tls_sock, 'DATA', 354)
        print(">>> [wysyłanie wiadomości z załącznikiem]")
        tls_sock.sendall(message.encode())
        response = get_response(tls_sock)
        if not response.startswith("250"):
            raise Exception(f"Email not accepted: {response}")

        send_command(tls_sock, 'QUIT', 221)
        print("Email z załącznikiem wysłany pomyślnie!")

    except Exception as e:
        print(f"Błąd: {e}")
    finally:
        try:
            tls_sock.close()
        except:
            sock.close()

if __name__ == "__main__":
    main()