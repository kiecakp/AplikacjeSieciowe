"""
Zmodyfikuj program numer 3 z laboratorium numer 9 w taki sposób, aby program pobierał z serwera
obrazek tylko wtedy, gdy nie zmienił się on od ostatniego pobrania. Jakich nagłówków HTTP należy użyć?

- ETag - unikalny identyfikator wersji zasobu, który serwer umieszcza w odpowiedzi; klient przechowuje 
        go i wysyła w kolejnych żądaniach w nagłówku If-None-Match, aby sprawdzić, czy zasób się zmienił
- Last-Modified - data ostatniej modyfikacji zasobu; klient przechowuje tę datę i wysyła w nagłówku 
        If-Modified-Since, aby sprawdzić, czy zasób został zmieniony od tego czasu
- If-None-Match - nagłówek wysyłany przez klienta z wartością ETag, aby sprawdzić, czy zasób się zmienił; 
        jeśli ETag się nie zgadza, serwer zwraca aktualną wersję zasobu
- If-Modified-Since - nagłówek wysyłany przez klienta z datą z Last-Modified, aby sprawdzić, czy zasób 
        został zmieniony od tego czasu; jeśli zasób nie został zmieniony, serwer zwraca status 304 Not Modified, 
        a klient może użyć lokalnej kopii zasobu zamiast pobierać go ponownie.
- Range - jeśli zasób się zmienił, można użyć tego nagłówka, aby pobrać tylko fragment pliku (np. Range: bytes=0-999), 
        co jest szczególnie przydatne dla dużych plików, takich jak obrazki.
- 304 Not Modified - status HTTP zwracany przez serwer, gdy zasób nie został zmieniony; klient powinien 
        wtedy użyć lokalnej kopii zasobu zamiast pobierać go ponownie.
"""

import socket
import os
import json

HOST = "212.182.24.27"
PORT = 8080
PATH = "/image.jpg"

# Ścieżka do zapisanego obrazka i pliku z metadanymi (ETag, Last-Modified)
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE  = os.path.join(SCRIPT_DIR, "zad6_obrazek.jpg")
METADATA_FILE = os.path.join(SCRIPT_DIR, "zad6_metadata.json")


# helpers
def load_metadata() -> dict:
    # Wczytuje zapisane metadane z poprzedniego pobrania (ETag, Last-Modified).
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_metadata(meta: dict):
    # Zapisuje metadane po udanym pobraniu obrazka.
    with open(METADATA_FILE, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[+] Metadane zapisane: {meta}")

def parse_headers(raw: bytes) -> dict:
    # Parsuje surowe nagłówki HTTP i zwraca słownik klucz→wartość (małe litery).
    headers = {}
    lines = raw.decode("utf-8", errors="replace").splitlines()
    status_line = lines[0] if lines else ""
    for line in lines[1:]:
        if ":" in line:
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()
    return status_line, headers

def send_request(method: str, extra_headers: dict) -> tuple[str, dict, bytes]:
    # Buduje i wysyła żądanie HTTP; zwraca (status_line, headers_dict, body).
    request = f"{method} {PATH} HTTP/1.1\r\n"
    request += f"Host: {HOST}:{PORT}\r\n"
    request += "Accept: image/jpeg,image/*;q=0.9,*/*;q=0.8\r\n"
    request += "Accept-Encoding: identity\r\n"
    request += "Connection: close\r\n"
    for key, value in extra_headers.items():
        request += f"{key}: {value}\r\n"
    request += "\r\n"   # pusta linia kończy nagłówki

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

        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

    if b"\r\n\r\n" in response:
        raw_headers, body = response.split(b"\r\n\r\n", 1)
    else:
        raw_headers, body = response, b""

    status_line, headers = parse_headers(raw_headers)
    return status_line, headers, body

def fetch_in_parts(total_size: int, conditional_headers: dict) -> bytes:
    # Pobiera plik w 3 częściach (Range), każda przez osobne połączenie TCP.
    part_size = total_size // 3
    ranges = [
        (0,             part_size - 1),
        (part_size,     2 * part_size - 1),
        (2 * part_size, total_size - 1),
    ]

    parts = []
    for i, (start, end) in enumerate(ranges):
        print(f"[*] Pobieranie części {i+1}/3: bytes={start}-{end} ...")

        # Łączymy nagłówki warunkowe z nagłówkiem Range
        headers = {**conditional_headers, "Range": f"bytes={start}-{end}"}
        status, _, body = send_request("GET", headers)
        print(f"    Status: {status} | odebrano: {len(body)} B")

        if "206" not in status and "200" not in status:
            print(f"[-] Nieoczekiwany status: {status}")
            exit(1)

        parts.append(body)

    return b"".join(parts)


# główna logika 
def main():
    metadata = load_metadata()
    etag          = metadata.get("etag")
    last_modified = metadata.get("last_modified")
    image_exists  = os.path.exists(OUTPUT_FILE)

    print(f"[*] Poprzednie metadane: ETag={etag!r}, Last-Modified={last_modified!r}")

    # KROK 1: HEAD — poznajemy rozmiar i sprawdzamy wersję zasobu
    # Nagłówki warunkowe If-None-Match / If-Modified-Since mówią serwerowi:
    # "odeślij mi zasób tylko jeśli zmienił się od ostatniego pobrania"
    conditional_headers = {}
    if etag and image_exists:
        # ETag ma wyższy priorytet niż Last-Modified (bardziej precyzyjny)
        conditional_headers["If-None-Match"] = etag
    elif last_modified and image_exists:
        conditional_headers["If-Modified-Since"] = last_modified

    print("\n[*] Krok 1: HEAD — sprawdzam aktualność obrazka na serwerze...")
    status_head, headers_head, _ = send_request("HEAD", conditional_headers)
    print(f"    Status HEAD: {status_head}")
    print(f"    Nagłówki:    {headers_head}")

    # KROK 2: Reagujemy na odpowiedź serwera
    if "304" in status_head:
        # Serwer potwierdził: zasób NIE zmienił się — nie pobieramy ponownie
        print("\n[+] 304 Not Modified — obrazek nie zmienił się, pomijam pobieranie.")
        print(f"[+] Używam zapisanego pliku: {OUTPUT_FILE}")
        return

    if "200" not in status_head:
        print(f"[-] Nieoczekiwany status HEAD: {status_head}")
        exit(1)

    # KROK 3: Zasób się zmienił (lub pobieramy po raz pierwszy) → pobieramy
    # Odczytujemy nowy rozmiar pliku
    content_length = headers_head.get("content-length")
    if not content_length:
        print("[-] Brak Content-Length w odpowiedzi HEAD.")
        exit(1)
    total_size = int(content_length)
    print(f"\n[+] Rozmiar pliku: {total_size} B — pobieram w 3 częściach...")

    # Przy właściwym GET nie wysyłamy już nagłówków warunkowych
    # (serwer i tak potwierdził 200 — zasób jest nowy)
    image_data = fetch_in_parts(total_size, {})

    # KROK 4: Zapis obrazka
    with open(OUTPUT_FILE, "wb") as f:
        f.write(image_data)
    print(f"\n[+] Obrazek zapisany: {OUTPUT_FILE} ({len(image_data)} B)")

    # Weryfikacja sygnatury JPEG (FF D8 FF)
    if image_data[:3] == b"\xff\xd8\xff":
        print("[+] Weryfikacja: poprawny plik JPEG ✓")
    else:
        print(f"[-] Nieoczekiwana sygnatura: {image_data[:3].hex()}")

    # KROK 5: Zapisujemy nowe metadane na kolejne uruchomienie
    new_meta = {}
    if "etag" in headers_head:
        new_meta["etag"] = headers_head["etag"]
    if "last-modified" in headers_head:
        new_meta["last_modified"] = headers_head["last-modified"]
    save_metadata(new_meta)


if __name__ == "__main__":
    main()