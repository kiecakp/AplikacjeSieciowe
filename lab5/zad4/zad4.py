"""
Napisz parę programów - klienta i serwer, w których porównasz czas przesyłu 
pakietów za pomocą gniazda TCP i gniazda UDP. Następnie, po przeprowadzonym 
teście, odpowiedz na pytania:
    • Dla którego z gniazd czas jest krótszy?
    • Z czego wynika krótszy czas?
    • Jakie są zalety / wady obu rozwiązań?
"""

import socket
import threading

HOST = '127.0.0.1'
TCP_PORT = 9001
UDP_PORT = 9002
BUFOR = 4096

def serwer_tcp():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, TCP_PORT))
        s.listen(1)
        print(f"[TCP] Serwer nasłuchuje na {HOST}:{TCP_PORT}...")

        conn, addr = s.accept()
        with conn:
            print(f"[TCP] Połączono z {addr}.")
            while True:
                data = conn.recv(BUFOR)
                if not data:
                    break
                conn.sendall(data)
            
            print(f"[TCP] Połączenie z {addr} zakończone.")

def serwer_udp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, UDP_PORT))
        print(f"[UDP] Serwer nasłuchuje na {HOST}:{UDP_PORT}...")

        while True:
            data, addr = s.recvfrom(BUFOR)
            if data == b'STOP':
                print(f"[UDP] Otrzymano sygnał STOP od {addr}. Zakończenie serwera.")
                break
            s.sendto(data, addr)

if __name__ == "__main__":
    t_tcp = threading.Thread(target=serwer_tcp)
    t_udp = threading.Thread(target=serwer_udp)

    t_tcp.start()
    t_udp.start()

    t_tcp.join()
    t_udp.join()