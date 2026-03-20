"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie UDP, dla podłączającego się klienta, będzie odbierał 
liczbę, operator i liczbę, a następnie odsyłał użytkownikowi wynik 
działania, przez niego przesłanego.
"""

#!/usr/bin/env python

import socket

HOST = '127.0.0.1'
PORT = 9003

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))

print(f"Serwer KALKULATOR działa na {HOST}:{PORT}")

try:
    while True:
        data, address = server.recvfrom(1024)
        msg = data.decode('utf-8').strip()
        print(f"Otrzymano od {address}: {msg}")

        try:
            parts = msg.split()
            if len(parts) != 3:
                raise ValueError("Nieprawidlowy format.")
            
            num1 = float(parts[0])
            operator = parts[1]
            num2 = float(parts[2])

            if operator == '+':
                result = num1 + num2
            elif operator == '-':
                result = num1 - num2
            elif operator == '*':
                result = num1 * num2
            elif operator == '/':
                if num2 == 0:
                    raise ValueError("Nie można dzielić przez zero.")
                result = num1 / num2
            else:
                raise ValueError("Nieznany operator.")
            
            response = str(result)

        except ZeroDivisionError as e:
            response = f"Error: {e}"
        except ValueError as e:
            response = f"Error: {e}"

        server.sendto(response.encode('utf-8'), address)
        print(f"Wysłano do {address}: {response}")

finally:
    server.close()