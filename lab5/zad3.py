"""
Port-knocking jest metodą pozwalającą na nawiązanie zdalnego połączenia z usługami 
działającymi na komputerze, do którego dostęp został ograniczony np. za pomocą zapory 
sieciowej, umożliwiającą odróżniania prób połączeń, które powinny i nie powinny być 
zrealizowane. Inaczej mówiąc, to metoda ustanawiania połączenia z hostem o zamkniętych portach.

Pod adresem 212.182.24.27 na porcie TCP o numerze 2913 działa ukryta usługa. Usługa 
jest zabezpieczona metodą port knocking - po otrzymaniu od klienta odpowiedniej 
sekwencji pakietów UDP na odpowiednie porty, otwiera wspomniany wyżej port TCP. Napisz 
program klienta, który odgadnie sekwencję portów UDP, a następnie odbierze od serwera wiadomość 
na porcie TCP.

Uwaga: Aby znaleźć porty UDP, składające się na sekwencję otwarcia docelowego portu TCP, wysyłaj
do serwera wiadomość o treści PING. W przypadku, gdy uda się znaleźć port UDP, należący do sekwencji
otwierającej port TCP, serwer odeśle wiadomość PONG. Porty UDP, które wchodzą w skład sekwencji
kończą się na 666. Usługa działająca na ukrytym porcie, jeśli uda się ją znaleźć, zwraca w odpowiedzi
tekst: Congratulations! You found the hidden.
"""

import socket
import time

HOST = '212.182.24.27'
TCP_PORT = 2913

def znajdz_porty_udp():
    # skanuje porty UDP konczace sie na 666 i zwraca te odpowiadajace PONG
    porty_sekwencji = []

    # porty konczace sie na 666: 666, 1666, 2666, ..., 65666
    kandydaci = [p for p in range(1, 65536) if str(p).endswith('666')]
    print("Skanowanie portów UDP kończących się na 666...")

    for port in kandydaci:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
                udp.settimeout(1)
                udp.sendto(b'PING', (HOST, port))
                try:
                    odpowiedz, _ = udp.recvfrom(1024)
                    if odpowiedz.strip() == b'PONG':
                        print(f"[+] PONG na porcie UDP {port}!")
                        porty_sekwencji.append(port)
                except socket.timeout:
                    pass
        except Exception as e:
            print(f"[-] Błąd na porcie {port}: {e}")
    
    return porty_sekwencji

def wykonaj_port_knocking(porty):
    # Wysyła sekwencję UDP na znalezione porty.
    print(f"\n[*] Wykonuję port-knocking na portach: {porty}")

    for port in porty:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            udp.sendto(b'PING', (HOST, port))
            print(f"[*] Knock -> UDP:{port}")
            time.sleep(0.5)

def polacz_tcp():
    # Próbuje połączyć się z ukrytą usługą TCP.
    print(f"\n[*] Łączę się z {HOST}:{TCP_PORT}...")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
            tcp.settimeout(5)
            tcp.connect((HOST, TCP_PORT))
            odpowiedz = tcp.recv(1024)
            print(f"[+] Odpowiedź serwera: {odpowiedz.decode('utf-8', errors='ignore').strip()}")
    except socket.timeout:
        print("[-] Timeout - port nadal zamknięty. Spróbuj innej kolejności.")
    except ConnectionRefusedError:
        print("[-] Połączenie odrzucone - port nadal zamknięty.")

def main():
    # Krok 1: znajdź porty UDP
    porty = znajdz_porty_udp()
    
    if not porty:
        print("[-] Nie znaleziono żadnych portów UDP. Sprawdź połączenie z serwerem.")
        return
    
    print(f"\n[+] Znaleziono porty sekwencji: {porty}")
    
    # Krok 2: port-knocking w znalezionej kolejności
    wykonaj_port_knocking(porty)
    
    # Krok 3: połącz się z usługą TCP
    polacz_tcp()

    # Krok 4: jeśli nie zadziałało, spróbuj permutacji kolejności
    if len(porty) > 1:
        from itertools import permutations
        print("\n[*] Próbuję różnych kolejności port-knockingu...")
        for perm in permutations(porty):
            if list(perm) == porty:
                continue  # już próbowaliśmy
            print(f"\n[*] Kolejność: {list(perm)}")
            wykonaj_port_knocking(list(perm))
            polacz_tcp()
            time.sleep(1)

if __name__ == "__main__":
    main()