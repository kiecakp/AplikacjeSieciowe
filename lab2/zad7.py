"""
Zmodyfikuj program numer 6 z lab1 w ten sposob, aby oprocz wyswietlania
informacji o tym czy port jest zamkniety, czy otwarty, klient wyswietla 
rowniez informacje o tym jaka usluga jest uruchomiona na danym porcie.
"""

import socket
import sys

def zad6():
    if len(sys.argv) != 3:
        print("Użycie: python zad.py <adres_serwera> <numer_portu>")
        return
    
    server_address = sys.argv[1]
    port = int(sys.argv[2])

    try:
        with socket.create_connection((server_address, port), timeout=0.5) as sock:
            print(f"Połączenie z {server_address}:{port} zostało nawiązane :3")

            service = socket.getservbyport(port)
            print(f"Usługa uruchomiona na porcie {port}: {service}")

    except (socket.timeout, socket.error) as e:
        print(f"Nie można nawiązać połączenia z {server_address}:{port} :(")

zad6()