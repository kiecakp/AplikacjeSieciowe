"""
Pod adresem 212.182.24.27 na porcie TCP o numerze 8080 działa serwer obsługujący protokół HTTP w
wersji 1.1. Pod odnośnikiem /image.jpg udostępnia obrazek. Napisz program klienta, który połączy się
z serwerem, a następnie pobierze z serwera obrazek w 3 częściach i po odebraniu wszystkich części złoży
go w całość. Jakich nagłówków HTTP należy użyć?

- Head - zamiast GET, żeby pobrać tylko nagłówki i poznać rozmiar pliku (Content-Length)
- Range - kluczowy nagłówek, który pozwala pobrać tylko fragment pliku (np. Range: bytes=0-999)
- Accept - określa, jakie typy treści klient jest w stanie zaakceptować (np. image/jpeg)
- Accept-Encoding - preferencje dotyczące kompresji (np. identity, żeby wyłączyć kompresję)
- Connection - close, żeby serwer zamknął połąc

!! W trakcie testów serwer 212.182.24.27:8080 nie był osiągalny. Próby połączenia przy użyciu klienta 
TCP (nc) kończyły się timeoutem, a host nie odpowiadał na pakiety ICMP (ping). W związku z tym nie było 
możliwe zweryfikowanie działania klienta HTTP mimo poprawnej implementacji programu.
"""

import socket
import os

HOST = "212.182.24.27"
PORT = 8080
PATH = "/image.jpg"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zad3_obrazek.jpg")

def send_request(host, port, path, headers):
    # Wysyła żądanie HTTP i zwraca (nagłówki_bytes, ciało_bytes).
    request = f"GET {path} HTTP/1.1\r\n"
    request += f"Host: {host}:{port}\r\n"
    for key, value in headers.items():
        request += f"{key}: {value}\r\n"
    request += "Connection: close\r\n\r\n"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        
        try:
            sock.connect((HOST, PORT))
        except socket.timeout:
            print("[-] Timeout: serwer nie odpowiada.")
            exit(1)
        except OSError as e:
            print(f"[-] Błąd połączenia: {e}")
            exit(1)

        sock.sendall(request.encode("utf-8"))

        response_bytes = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_bytes += chunk

    separator = b"\r\n\r\n"
    if separator in response_bytes:
        headers_raw, body = response_bytes.split(separator, 1)
    else:
        headers_raw, body = response_bytes, b""

    return headers_raw, body


# KROK 1: Żądanie HEAD — pobieramy rozmiar pliku z Content-Length
# Nagłówek: nie pobieramy ciała, tylko metadane
print("[*] Krok 1: Wysyłanie żądania HEAD aby poznać rozmiar pliku...")

request_head = f"HEAD {PATH} HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nConnection: close\r\n\r\n"
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(5)
    
    try:
        sock.connect((HOST, PORT))
    except socket.timeout:
        print("[-] Timeout: serwer nie odpowiada.")
        exit(1)
    except OSError as e:
        print(f"[-] Błąd połączenia: {e}")
        exit(1)

    sock.sendall(request_head.encode("utf-8"))
    head_response = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        head_response += chunk

head_text = head_response.decode("utf-8", errors="replace")
print("--- Odpowiedź HEAD ---")
print(head_text)
print("")

# Wyciągamy Content-Length z nagłówków
total_size = None
for line in head_text.splitlines():
    if line.lower().startswith("content-length:"):
        total_size = int(line.split(":", 1)[1].strip())
        break

if total_size is None:
    print("[-] Nie można odczytać Content-Length. Próba pobrania bez podziału.")
    exit(1)

print(f"[+] Rozmiar pliku: {total_size} bajtów")


# KROK 2: Obliczamy zakresy dla 3 części
# Nagłówek Range: bytes=START-END  (zakresy włączne, liczone od 0)
part_size = total_size // 3
ranges = [
    (0,              part_size - 1),
    (part_size,      2 * part_size - 1),
    (2 * part_size,  total_size - 1),      # ostatnia część — do końca pliku
]

print(f"\n[*] Podział na 3 części:")
for i, (start, end) in enumerate(ranges):
    print(f"    Część {i+1}: bajty {start}-{end} ({end - start + 1} bajtów)")


# KROK 3: Pobieramy każdą część osobnym połączeniem TCP
# Kluczowy nagłówek: Range: bytes=START-END
# Serwer odpowiada kodem 206 Partial Content
parts = []
for i, (start, end) in enumerate(ranges):
    print(f"\n[*] Pobieranie części {i+1}: Range: bytes={start}-{end} ...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) "
                      "AppleWebKit/537.75.14 (KHTML, like Gecko) "
                      "Version/7.0.3 Safari/7046A194A",
        "Accept":          "image/jpeg,image/*;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "identity",
        "Range":           f"bytes={start}-{end}",   # kluczowy nagłówek!
    }

    headers_raw, body = send_request(HOST, PORT, PATH, headers)
    status_line = headers_raw.splitlines()[0].decode("utf-8")
    print(f"    Status: {status_line}")

    if "206" not in status_line and "200" not in status_line:
        print(f"[-] Nieoczekiwany status dla części {i+1}: {status_line}")
        exit(1)

    print(f"    Odebrano: {len(body)} bajtów")
    parts.append(body)


# KROK 4: Składamy części w całość
print("\n[*] Składanie części w całość...")
full_image = b"".join(parts)
print(f"[+] Łączny rozmiar po złożeniu: {len(full_image)} bajtów (oczekiwano: {total_size})")

with open(OUTPUT_FILE, "wb") as f:
    f.write(full_image)

print(f"[+] Obrazek zapisany jako: {OUTPUT_FILE}")

# Weryfikacja — JPEG zaczyna się od FF D8 FF
with open(OUTPUT_FILE, "rb") as f:
    magic = f.read(3)
if magic == b"\xff\xd8\xff":
    print("[+] Weryfikacja: plik to poprawny JPEG ✓")
else:
    print(f"[-] Uwaga: nieoczekiwany nagłówek pliku: {magic.hex()}")