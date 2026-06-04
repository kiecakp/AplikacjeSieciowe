"""
Pod adresem httpbin.org na porcie TCP o numerze 80 działa serwer obsługujący protokół HTTP w
wersji 1.1. Pod odnośnikiem /post udostępnia formularz z polami do wypełnienia.
Napisz program klienta, który połączy się z serwerem, a następnie uzupełni formularz danymi pobranymi
od użytkownika, a następnie prześle go do serwera i odbierze odpowiedź.

Aby sprawdzić, jak wygląda żądanie HTTP potrzebne do wypełnienia i wysłania formularza:
    • jakie nagłówki HTTP są wykorzystywane,
    • jak wygląda ciało zapytania,
podsłuchaj komunikację z serwerem za pomocą Wiresharka, tj. uruchom przeglądarkę oraz Wiresharka;
uzupełnij i zatwierdź formularz ręcznie za pomocą przeglądarki, a następnie sprawdź pakiety podsłuchane podczas komunikacji z serwerem httpbin.org. Możesz użyć filtrów Wiresharka: http.request oraz
http.response (http.request || http.response).
"""

import socket

def get_user_data():
    print("Klient HTTP - formularz httpbin.org/post")
    first_name = input("Podaj imię:       ")
    last_name  = input("Podaj nazwisko:   ")
    email      = input("Podaj e-mail:     ")
    message    = input("Podaj wiadomość:  ")
    return first_name, last_name, email, message

def url_encode(data: dict) -> str:
    # Prosta implementacja kodowania application/x-www-form-urlencoded.
    # Znaki, które nie wymagają kodowania procentowego
    safe_chars = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789-_.~"
    )

    def encode(value: str) -> str:
        result = []
        for byte in value.encode("utf-8"):
            char = chr(byte)
            if char in safe_chars:
                result.append(char)
            elif char == " ":
                # Spacja kodowana jako plus (standard formularzy HTML)
                result.append("+")
            else:
                # Pozostałe znaki kodowane procentowo, np. @ -> %40
                result.append(f"%{byte:02X}")
        return "".join(result)

    return "&".join(f"{encode(k)}={encode(v)}" for k, v in data.items())

def send_form(host: str, port: int, path: str, data: dict) -> str:
    # Kodujemy dane formularza do ciała żądania
    body = url_encode(data)
    content_length = len(body.encode("utf-8"))

    # Budujemy żądanie HTTP/1.1 zgodnie ze standardem RFC 7230
    request = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Type: application/x-www-form-urlencoded\r\n"
        f"Content-Length: {content_length}\r\n"
        f"Connection: close\r\n"   # serwer zamknie połączenie po odpowiedzi
        f"\r\n"                    # pusta linia oddziela nagłówki od ciała
        f"{body}"
    )

    print("\n--- Wysyłane żądanie HTTP ---")
    print(request)

    # Otwieramy gniazdo TCP i łączymy się z serwerem
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.sendall(request.encode("utf-8"))

        # Odbieramy odpowiedź w pętli aż serwer zamknie połączenie
        buffer = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buffer += chunk

    return buffer.decode("utf-8", errors="replace")

def parse_response(raw: str):
    # Rozdziela surową odpowiedź HTTP na nagłówki i ciało.
    if "\r\n\r\n" in raw:
        headers, body = raw.split("\r\n\r\n", 1)
    else:
        headers, body = raw, ""
    return headers, body

if __name__ == "__main__":
    HOST = "httpbin.org"
    PORT = 80
    PATH = "/post"

    first_name, last_name, email, message = get_user_data()

    # Słownik pól formularza wysyłanych do serwera
    form_data = {
        "first_name": first_name,
        "last_name":  last_name,
        "email":      email,
        "message":    message,
    }

    response_raw = send_form(HOST, PORT, PATH, form_data)

    response_headers, response_body = parse_response(response_raw)

    print("\n--- Nagłówki odpowiedzi ---")
    print(response_headers)
    print("\n--- Ciało odpowiedzi (JSON od serwera) ---")
    print(response_body)