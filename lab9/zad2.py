"""
Pod adresem httpbin.org na porcie TCP o numerze 80 działa serwer obsługujący protokół HTTP w
wersji 1.1. Pod odnośnikiem /image/png udostępnia obrazek. Napisz program klienta, który połączy się
z serwerem, a następnie pobierze obrazek i zapisze go na dysku. Jakich nagłówków HTTP należy użyć?

- Host - wymagany w HTTP/1.1, określa nazwę hosta, do którego kierowane jest żądanie
- Accept - określa, jakie typy treści klient jest w stanie zaakceptować (np. image/png)
- Accept-Encoding - preferencje dotyczące kompresji (np. identity, żeby wyłączyć kompresję)
- Connection - close, żeby serwer zamknął połączenie po wysłaniu odpowiedzi
"""

import socket
import os

# Parametry połączenia
HOST = "httpbin.org"
PORT = 80
PATH = "/image/png"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zad2_obrazek.png")

# Żądanie HTTP — kluczowy nagłówek to Accept: image/png
request = (
    f"GET {PATH} HTTP/1.1\r\n"
    f"Host: {HOST}\r\n"
    f"User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) "
    f"AppleWebKit/537.75.14 (KHTML, like Gecko) "
    f"Version/7.0.3 Safari/7046A194A\r\n"
    f"Accept: image/png,image/*;q=0.9,*/*;q=0.8\r\n"
    f"Accept-Encoding: identity\r\n"   # wyłączamy kompresję — dane binarne nie wymagają dodatkowego kodowania
    f"Connection: close\r\n"
    f"\r\n"
)

print(f"[*] Łączenie z {HOST}:{PORT}...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    print("[*] Połączono. Wysyłanie żądania HTTP...")

    sock.sendall(request.encode("utf-8"))

    # Odbieramy RAW bajty (obrazek jest binarny!)
    response_bytes = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response_bytes += chunk

print(f"[*] Odebrano {len(response_bytes)} bajtów.")

# Rozdzielamy nagłówki od ciała po sekwencji \r\n\r\n (bajty!)
# WAŻNE: nie dekodujemy całości do stringa — ciało to dane binarne
separator = b"\r\n\r\n"
if separator in response_bytes:
    headers_raw, body = response_bytes.split(separator, 1)
else:
    headers_raw, body = response_bytes, b""

# Nagłówki możemy bezpiecznie zdekodować jako tekst
print("\n--- Nagłówki odpowiedzi serwera ---")
print(headers_raw.decode("utf-8", errors="replace"))

first_line = headers_raw.splitlines()[0].decode("utf-8")
print(f"[*] Status: {first_line}")

if "200" in first_line:
    # Zapisujemy ciało jako plik binarny
    with open(OUTPUT_FILE, "wb") as f:
        f.write(body)
    print(f"[+] Obrazek zapisany jako: {OUTPUT_FILE}")
    print(f"[+] Rozmiar pliku: {os.path.getsize(OUTPUT_FILE)} bajtów")

    # Weryfikacja — PNG zaczyna się od stałego nagłówka \x89PNG
    with open(OUTPUT_FILE, "rb") as f:
        magic = f.read(4)
    if magic == b"\x89PNG":
        print("[+] Weryfikacja: plik to poprawny PNG ✓")
    else:
        print(f"[-] Uwaga: nieoczekiwany nagłówek pliku: {magic}")
else:
    print(f"[-] Serwer zwrócił nieoczekiwany status: {first_line}")
    print(headers_raw.decode("utf-8", errors="replace"))