"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na określonym porcie TCP, będzie
serwerem HTTP. Obsłuż wybrane nagłówki i co najmniej jeden kod błędu (np. 404). Jako przykładowe
pliki serwera (stronę główną i stronę błędu) możesz wykorzystać pliki dostępne na stronie przedmiotu
"""

import socket
import threading
import os
import mimetypes
from datetime import datetime, timezone

# Konfiguracja serwera
HOST       = "127.0.0.1"
PORT       = 8080
BUFFER     = 4096
# Katalog z plikami serwowanymi klientom (obok skryptu)
WWW_ROOT   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zad7_www")


# Pomocnicze funkcje 

def log(client_addr: tuple, method: str, path: str, status: int):
    # Loguje każde żądanie w stylu Combined Log Format.
    ts = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    print(f"[{ts}] {client_addr[0]}:{client_addr[1]}  {method} {path}  →  {status}")

def now_http() -> str:
    # Zwraca aktualny czas w formacie wymaganym przez HTTP (RFC 7231).
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

def file_mtime_http(path: str) -> str:
    # Zwraca czas ostatniej modyfikacji pliku w formacie HTTP.
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

def build_response(status_code: int, status_text: str,
                   body: bytes, content_type: str,
                   extra_headers: dict = None) -> bytes:
    #Składa kompletną odpowiedź HTTP/1.1.
    headers  = f"HTTP/1.1 {status_code} {status_text}\r\n"
    headers += f"Date: {now_http()}\r\n"
    headers += f"Server: PythonHTTP/1.0\r\n"
    headers += f"Content-Type: {content_type}\r\n"
    headers += f"Content-Length: {len(body)}\r\n"
    headers += f"Connection: close\r\n"
    if extra_headers:
        for k, v in extra_headers.items():
            headers += f"{k}: {v}\r\n"
    headers += "\r\n"   # pusta linia oddziela nagłówki od ciała
    return headers.encode("utf-8") + body

def load_file(filepath: str) -> bytes:
    with open(filepath, "rb") as f:
        return f.read()

def error_page(code: int, text: str) -> bytes:
    # Generuje prostą stronę błędu HTML, jeśli brak pliku w www/.
    custom = os.path.join(WWW_ROOT, f"{code}.html")
    if os.path.exists(custom):
        return load_file(custom)
    return (
        f"<!DOCTYPE html><html><head><title>{code} {text}</title></head>"
        f"<body><h1>{code} {text}</h1></body></html>"
    ).encode("utf-8")


# Parsowanie żądania
def parse_request(raw: bytes) -> tuple[str, str, str, dict]:
    # Parsuje surowe żądanie HTTP.
    # Zwraca (method, path, version, headers_dict).
    try:
        # Rozdzielamy nagłówki od ciała (nas interesują tylko nagłówki)
        header_part = raw.split(b"\r\n\r\n", 1)[0].decode("utf-8", errors="replace")
        lines = header_part.splitlines()
        method, path, version = lines[0].split(" ", 2)

        headers = {}
        for line in lines[1:]:
            if ":" in line:
                key, _, value = line.partition(":")
                headers[key.strip().lower()] = value.strip()

        # Usuwamy query string z ścieżki
        path = path.split("?")[0]
        return method.upper(), path, version.strip(), headers
    except Exception:
        return "GET", "/", "HTTP/1.1", {}


# Obsługa żądania

def handle_request(method: str, path: str, req_headers: dict) -> bytes:
    """
    Główna logika serwera — zwraca gotową odpowiedź HTTP jako bytes.
    Obsługiwane metody: GET, HEAD.
    Obsługiwane kody: 200, 304, 400, 404, 405.
    """

    # 400 Bad Request — nieobsługiwana wersja protokołu
    # (akceptujemy tylko HTTP/1.0 i HTTP/1.1)

    # 405 Method Not Allowed — obsługujemy tylko GET i HEAD
    if method not in ("GET", "HEAD"):
        body = error_page(405, "Method Not Allowed")
        return build_response(405, "Method Not Allowed", body, "text/html; charset=utf-8",
                              {"Allow": "GET, HEAD"})

    # Mapujemy ścieżkę URL na plik w katalogu www/
    # Zabezpieczenie przed path traversal (../../etc/passwd)
    safe_path = os.path.normpath(path.lstrip("/"))
    if safe_path.startswith(".."):
        body = error_page(403, "Forbidden")
        return build_response(403, "Forbidden", body, "text/html; charset=utf-8")

    # Domyślny plik dla katalogu głównego
    if safe_path == "." or safe_path == "":
        safe_path = "index.html"

    filepath = os.path.join(WWW_ROOT, safe_path)

    # 404 Not Found — plik nie istnieje
    if not os.path.isfile(filepath):
        body = error_page(404, "Not Found")
        return build_response(404, "Not Found", body, "text/html; charset=utf-8")

    # Wykrywamy typ MIME na podstawie rozszerzenia pliku
    mime, _ = mimetypes.guess_type(filepath)
    if mime is None:
        mime = "application/octet-stream"
    if mime.startswith("text/"):
        mime += "; charset=utf-8"

    # ETag = rozmiar pliku + czas modyfikacji (prosta, deterministyczna wersja)
    mtime     = os.path.getmtime(filepath)
    file_size = os.path.getsize(filepath)
    etag      = f'"{file_size}-{int(mtime)}"'
    last_mod  = file_mtime_http(filepath)

    extra = {
        "ETag":          etag,
        "Last-Modified": last_mod,
    }

    # --- Obsługa warunkowego GET ---

    # If-None-Match: klient odsyła ETag — sprawdzamy czy zasób się zmienił
    if_none_match = req_headers.get("if-none-match")
    if if_none_match and if_none_match == etag:
        return build_response(304, "Not Modified", b"", mime, extra)

    # If-Modified-Since: klient podaje datę swojej kopii
    if_mod_since = req_headers.get("if-modified-since")
    if if_mod_since and if_mod_since == last_mod:
        return build_response(304, "Not Modified", b"", mime, extra)

    # --- Normalna odpowiedź 200 OK ---
    file_body = load_file(filepath)

    # HEAD — jak GET, ale bez ciała odpowiedzi
    if method == "HEAD":
        return build_response(200, "OK", b"", mime, extra)

    return build_response(200, "OK", file_body, mime, extra)

# Wątek klienta 

def handle_client(conn: socket.socket, addr: tuple):
    # Obsługuje pojedyncze połączenie TCP w osobnym wątku.
    try:
        raw = b""
        # Odbieramy dane aż do końca nagłówków (\r\n\r\n)
        while b"\r\n\r\n" not in raw:
            chunk = conn.recv(BUFFER)
            if not chunk:
                break
            raw += chunk

        if not raw:
            return

        method, path, version, req_headers = parse_request(raw)
        response = handle_request(method, path, req_headers)

        # Odczytujemy kod statusu z odpowiedzi do logowania
        status_code = int(response.split(b" ", 2)[1])
        log(addr, method, path, status_code)

        conn.sendall(response)
    except Exception as e:
        print(f"[!] Błąd obsługi klienta {addr}: {e}")
    finally:
        conn.close()


# Główna pętla serwera 

def run_server():
    # Tworzymy przykładowe pliki www/ jeśli katalog nie istnieje
    os.makedirs(WWW_ROOT, exist_ok=True)
    _create_default_files()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        # SO_REUSEADDR — pozwala od razu ponownie uruchomić serwer
        # po zamknięciu (bez czekania na wygaśnięcie TIME_WAIT)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT))
        server_sock.listen(10)
        print(f"[+] Serwer HTTP działa na http://{HOST}:{PORT}/")
        print(f"[+] Katalog www: {WWW_ROOT}")
        print(f"[+] Ctrl+C aby zatrzymać\n")

        while True:
            conn, addr = server_sock.accept()
            # Każde połączenie obsługujemy w osobnym wątku
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()


def _create_default_files():
    # Tworzy przykładowe pliki HTML jeśli jeszcze nie istnieją.
    index = os.path.join(WWW_ROOT, "index.html")
    err404 = os.path.join(WWW_ROOT, "404.html")

    if not os.path.exists(index):
        with open(index, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Strona główna</title>
    <style>
        body { font-family: monospace; max-width: 600px; margin: 60px auto; }
        h1   { color: #2c7be5; }
        code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>Serwer HTTP działa!</h1>
    <p>To jest strona główna serwera napisanego w Pythonie.</p>
    <ul>
        <li><a href="/index.html">Strona główna</a></li>
        <li><a href="/404.html">Strona błędu 404</a></li>
        <li><a href="/nieistniejacy.html">Test błędu 404</a></li>
    </ul>
    <p>Obsługiwane nagłówki: <code>ETag</code>, <code>Last-Modified</code>,
    <code>If-None-Match</code>, <code>If-Modified-Since</code></p>
</body>
</html>""")

    if not os.path.exists(err404):
        with open(err404, "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>404 Not Found</title>
    <style>
        body { font-family: monospace; max-width: 600px; margin: 60px auto; text-align: center; }
        h1   { font-size: 6rem; color: #e53e3e; margin: 0; }
        p    { color: #555; }
    </style>
</head>
<body>
    <h1>404</h1>
    <p>Strona nie została znaleziona.</p>
    <a href="/">← Wróć na stronę główną</a>
</body>
</html>""")


if __name__ == "__main__":
    run_server()