import socket
import sys

""" 
Napisz program, w którym pobierzesz od użytkownika nazwę
pliku tekstowego, a następnie skopiujesz go do pliku pod nazwą
'lab1zad1.txt'.
"""
def zad1():
    name = input("Podaj nazwę pliku tekstowego: ")

    with open(name, 'r') as source_file:
        with open('lab1zad1.txt', 'w') as file:
            file.write(source_file.read())

    print("Plik został skopiowany :3")

"""
Napisz program, w którym pobierzesz od użytkownika nazwę
pliku graficznego, a następnie skopiujesz go do pliku pod nazwą
'lab1zad1.png'.
"""
def zad2():
    name = input("Podaj nazwę pliku graficznego: ")

    with open(name, 'rb') as source_file:
        with open('lab1zad1.png', 'wb') as file:
            file.write(source_file.read())

    print("Plik został skopiowany :3")

"""
Napisz program, w którym pobierzesz od użytkownika adres IP, a
następnie sprawdzisz, czy jest on poprawnym adresem.
"""
def zad3():
    ip = input("Podaj adres IP: ")
    octets = ip.split('.')

    if len(octets) != 4:
        print("Adres IP jest niepoprawny :(")
        return
    
    for octet in octets:
        if not octet.isdigit():
            print("Adres IP jest niepoprawny :(")
            return
        
        num = int(octet)
        if num < 0 or num > 255:
            print("Adres IP jest niepoprawny :(")
            return
        
    print("Adres IP jest poprawny :3")

"""
Napisz program, który jako argument linii poleceń pobierze od
użytkownika adres IP, a następnie wyświetli odpowiadającą mu
nazwę hostname.
"""
def zad4():
    if len(sys.argv) != 2:
        print("Użycie: python zad.py <adres_ip>")
        return

    ip = sys.argv[1]

    try:
        hostname = socket.gethostbyaddr(ip)[0]
        print(f"Nazwa hostname dla adresu IP {ip } to: {hostname}")
    except socket.herror:
        print(f"Nie można znaleźć nazwy hostname dla adresu IP {ip}")

"""
Napisz program, który jako argument linii poleceń pobierze od
użytkownika hostname, a następnie wyświetli odpowiadający mu
adres IP.
"""
def zad5():
    if len(sys.argv) != 2:
        print("Użycie: python zad.py <hostname>")
        return
    
    hostname = sys.argv[1]

    try:
        ip = socket.gethostbyname(hostname)
        print(f"Adres IP dla hostname {hostname} to: {ip}")
    except socket.gaierror:
        print(f"Nie można znaleźć adresu IP dla hostname {hostname}")

"""
Napisz program, w którym połączysz się z serwerem na danym porcie
przy użyciu protokołu TCP. Adres serwera i numer portu pobierz
jako argumenty linii poleceń. Wyświetl informację, czy udało się
nawiązać połączenie. Program powinien akceptować adres w postaci
adresu IP jak i hostname.
"""
def zad6():
    if len(sys.argv) != 3:
        print("Użycie: python zad.py <adres_serwera> <numer_portu>")
        return
    
    server_address = sys.argv[1]
    port = int(sys.argv[2])

    try:
        with socket.create_connection((server_address, port), timeout=0.5) as sock:
            print(f"Połączenie z {server_address}:{port} zostało nawiązane :3")
    except (socket.timeout, socket.error) as e:
        print(f"Nie można nawiązać połączenia z {server_address}:{port} :(")

"""
Napisz program (skaner portów), który dla danego serwera przy
użyciu protokołu TCP będzie sprawdzał, jakie porty są otwarte.
Adres serwera pobierz jako argument linii poleceń. Program
powinien akceptować adres w postaci adresu IP jak i hostname.
"""
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
        
        sock.close()

# zad1()
# zad2()
# zad3()
# zad4()
# zad5()
# zad6()
# zad7()