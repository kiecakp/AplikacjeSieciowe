"""
Napisz program serwera, który działając pod adresem 127.0.0.1 oraz na 
określonym porcie TCP, będzie serwerem poczty, obsługującym protokół 
SMTP. Nie realizuj faktycznego wysyłania e-maila, tylko zasymuluj jego 
działanie tak, żeby napisany wcześniej klient SMTP myślał, że wiadomość 
została wysłana. Pamiętaj o obsłudze przypadku, gdy klient poda nie 
zaimplementowaną przez serwer komendę.
"""

import socket
import threading

HOST = '127.0.0.1'
PORT = 1025

def handle_client(conn, addr):
    print(f"[+] Połączono z {addr}")
    conn.sendall(b"220 Mock SMTP Server Ready\r\n")

    data_mode = False
    buffer = b""

    while True:
        data = conn.recv(1024)
        if not data:
            break
        buffer += data

        # rozdzielanie na linie
        while b'\r\n' in buffer:
            line_bytes, buffer = buffer.split(b'\r\n', 1)
            line = line_bytes.decode()
            print(f"<<< {line}")

            if data_mode:
                if line == '.':
                    data_mode = False
                    print("[+] Wiadomość odebrana (symulacja).")
                    conn.sendall(b"250 OK: Message accepted\r\n")
                else:
                    # w trybie DATA po prostu przechowujemy linie
                    pass
                continue

            cmd = line.split()[0].upper() if line else ""

            if cmd in ['EHLO', 'HELO']:
                conn.sendall(b"250-localhost Hello\r\n250-SIZE 35882577\r\n250-PIPELINING\r\n250 OK\r\n")
            elif cmd == 'MAIL':
                conn.sendall(b"250 OK\r\n")
            elif cmd == 'RCPT':
                conn.sendall(b"250 OK\r\n")
            elif cmd == 'DATA':
                conn.sendall(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                data_mode = True
            elif cmd == 'QUIT':
                conn.sendall(b"221 Bye\r\n")
                conn.close()
                print(f"[-] Rozłączono {addr}")
                return
            elif cmd == 'AUTH':
                conn.sendall(b"235 Authentication successful\r\n")
            else:
                conn.sendall(b"502 Command not implemented\r\n")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[+] Mock SMTP Server uruchomiony na {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[!] Serwer zatrzymany ręcznie")
    finally:
        server.close()

if __name__ == "__main__":
    main()