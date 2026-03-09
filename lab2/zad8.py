"""
Zmodyfikuj program numer 7 z lab1 w ten sposob aby oprocz wyswietlania
informacji o tym czy porty sa zamkniete czy otwarte, klient wyswietlal 
rowniez informacje o tym jaka usluga jest uruchomiona na danym porcie.
"""

import socket
import sys

def zad7():
    if len(sys.argv) != 2:
        print("Użycie: python zad.py <adres_serwera>")
        return
    
    server_address = sys.argv[1]

    print(f"Skanowanie portów dla {server_address}...")
    
    for port in range(1, 65536):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((server_address, port))
        
        if result == 0:
            print(f"Port {port} jest otwarty")

            try:
                service = socket.getservbyport(port)
                print(f"Usługa uruchomiona na porcie {port}: {service}")
            except socket.error:
                print(f"Nie można określić usługi na porcie {port}")

        sock.close()

zad7()