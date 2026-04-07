"""
Kod klienta
"""

import socket
import time

HOST = '127.0.0.1'
TCP_PORT = 9001
UDP_PORT = 9002
LICZBA_PAKIETOW = 1000
ROZMIAR_PAKIETU = 1024
BUFOR = 4096

def test_tcp():
    wiadomosc = b'X' * ROZMIAR_PAKIETU
    start = time.perf_counter()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, TCP_PORT))
        for _ in range(LICZBA_PAKIETOW):
            s.sendall(wiadomosc)
            odebrano = 0
            while odebrano < ROZMIAR_PAKIETU:
                chunk = s.recv(BUFOR)
                odebrano += len(chunk)

    czas = time.perf_counter() - start
    return czas

def test_udp():
    wiadomosc = b'X' * ROZMIAR_PAKIETU
    utracone = 0
    start = time.perf_counter()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1)
        for _ in range(LICZBA_PAKIETOW):
            s.sendto(wiadomosc, (HOST, UDP_PORT))
            try:
                s.recvfrom(BUFOR)
            except socket.timeout:
                utracone += 1

        s.sendto(b'STOP', (HOST, UDP_PORT))

    czas = time.perf_counter() - start
    return czas, utracone

def main():
    print(f"Test: {LICZBA_PAKIETOW} pakietów x {ROZMIAR_PAKIETU} bajtów")

    print("\n[*] Testuję TCP...")
    czas_tcp = test_tcp()
    print(f"[TCP] Czas: {czas_tcp:.4f}s")
    print(f"[TCP] Średnio na pakiet: {czas_tcp/LICZBA_PAKIETOW*1000:.4f} ms")

    print("\n[*] Testuję UDP...")
    czas_udp, utracone = test_udp()
    print(f"[UDP] Czas: {czas_udp:.4f}s")
    print(f"[UDP] Średnio na pakiet: {czas_udp/LICZBA_PAKIETOW*1000:.4f} ms")
    print(f"[UDP] Utracone pakiety: {utracone}/{LICZBA_PAKIETOW} ({utracone/LICZBA_PAKIETOW*100:.1f}%)")

    print("\nWYNIKI:")
    roznica = abs(czas_tcp - czas_udp)
    if czas_udp < czas_tcp:
        print(f"UDP był szybszy o {roznica:.4f}s ({roznica/czas_tcp*100:.1f}%)")
    else:
        print(f"TCP był szybszy o {roznica:.4f}s ({roznica/czas_udp*100:.1f}%)")

if __name__ == "__main__":
    main()