"""
Zmodyfikuj program nr 7 z laboratorium nr 3 w ten sposób, aby mieć 
pewność, że serwer w rzeczywistości odebrał / wysłał wiadomość o wymaganej 
długości.
"""

#!/usr/bin/env python

import socket, select
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 9007
MSG_LEN = 20

connected_clients_sockets = []

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(10)

connected_clients_sockets.append(server_socket)

print("[%s] TCP ECHO Server is waiting for incoming connections on port %s ... " % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), PORT))

while True:

    read_sockets, write_sockets, error_sockets = select.select(connected_clients_sockets, [], [])

    for sock in read_sockets:

        if sock == server_socket:
            sockfd, client_address = server_socket.accept()
            connected_clients_sockets.append(sockfd)
            print("[%s] Client %s connected ... " % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), client_address))

        else:
            try:
                # Odbieranie - pętla gwarantuje dokładnie MSG_LEN bajtów
                data = b''
                while len(data) < MSG_LEN:
                    chunk = sock.recv(MSG_LEN - len(data))
                    if not chunk:
                        raise ConnectionError("Klient rozłączył się")
                    data += chunk

                # Wysyłanie - pętla gwarantuje dokładnie MSG_LEN bajtów
                total_sent = 0
                while total_sent < MSG_LEN:
                    sent = sock.send(data[total_sent:])
                    if sent == 0:
                        raise ConnectionError("Klient rozłączył się")
                    total_sent += sent

                print("[%s] Sending back to client %s data: [\'%s\']... " % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), client_address, data))

            except:
                print("[%s] Client (%s) is offline" % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), client_address))
                sock.close()
                connected_clients_sockets.remove(sock)
                continue

server_socket.close()