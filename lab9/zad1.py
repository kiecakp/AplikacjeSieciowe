"""
Pod adresem httpbin.org na porcie TCP o numerze 80 działa serwer obsługujący protokół HTTP w wersji
1.1. Pod odnośnikiem /html udostępnia prostą stronę HTML. Napisz program klienta, który połączy się
z serwerem, a następnie pobierze treść strony i zapisze ją na dysku jako plik z rozszerzeniem *.html.
Spreparuj żądanie HTTP tak, aby serwer myślał, że żądanie przyszło od przeglądarki Safari 7.0.3.
Jakich nagłówków HTTP należy użyć?

- Host - wymagany w HTTP/1.1, określa nazwę hosta, do którego kierowane jest żądanie
- User-Agent - podszywanie się pod Safari 7.0.3
- Accept - określa, jakie typy treści klient jest w stanie zaakceptować (np. text/html)
- Accept-Language - preferencje językowe (np. pl-PL)
- Accept-Encoding - preferencje dotyczące kompresji (np. identity, żeby wyłączyć kompresję)
- Connection - close, żeby serwer zamknął połączenie po wysłaniu odpowiedzi
"""

import socket
import os

# Parametry połączenia
HOST = "httpbin.org"
PORT = 80
PATH = "/html"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zad1_strona.html")

# Nagłówki HTTP symulujące przeglądarkę Safari 7.0.3 (macOS Mavericks)
# User-Agent pochodzi z rzeczywistego Safari 7.0.3 na Mac OS X 10.9.3
request = (
    f"GET {PATH} HTTP/1.1\r\n"
    f"Host: {HOST}\r\n"
    f"User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) "
    f"AppleWebKit/537.75.14 (KHTML, like Gecko) "
    f"Version/7.0.3 Safari/7046A194A\r\n"
    f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
    f"Accept-Language: pl-PL,pl;q=0.8,en-US;q=0.5,en;q=0.3\r\n"
    f"Accept-Encoding: identity\r\n"   # wyłączamy kompresję, żeby łatwiej odczytać treść
    f"Connection: close\r\n"
    f"\r\n"
)

print(f"[*] Łączenie z {HOST}:{PORT}...")

# Tworzymy gniazdo TCP i łączymy się z serwerem
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    print("[*] Połączono. Wysyłanie żądania HTTP...")

    # Wysyłamy żądanie (zakodowane jako bajty)
    sock.sendall(request.encode("utf-8"))

    # Odbieramy odpowiedź w pętli, aż serwer zamknie połączenie
    response_bytes = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response_bytes += chunk

print(f"[*] Odebrano {len(response_bytes)} bajtów.")

# Dekodujemy całą odpowiedź
response = response_bytes.decode("utf-8", errors="replace")

# Rozdzielamy nagłówki HTTP od ciała odpowiedzi
# HTTP/1.1 używa sekwencji \r\n\r\n jako separatora
separator = "\r\n\r\n"
if separator in response:
    headers_raw, body = response.split(separator, 1)
else:
    headers_raw, body = response, ""

# Wyświetlamy nagłówki odpowiedzi serwera
print("\n--- Nagłówki odpowiedzi serwera ---")
print(headers_raw)
print("")

# Sprawdzamy kod statusu HTTP
first_line = headers_raw.splitlines()[0]
print(f"[*] Status: {first_line}")

if "200" in first_line:
    # Zapisujemy ciało odpowiedzi (treść HTML) do pliku
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"[+] Strona zapisana jako: {os.path.abspath(OUTPUT_FILE)}")
    print(f"[+] Rozmiar pliku: {os.path.getsize(OUTPUT_FILE)} bajtów")
else:
    print(f"[-] Serwer zwrócił nieoczekiwany status: {first_line}")
    print("Treść odpowiedzi:")
    print(body[:500])