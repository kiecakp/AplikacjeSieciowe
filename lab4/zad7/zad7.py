"""
Zmodyfikuj program nr 2 z laboratorium nr 3 w ten sposób, aby serwer 
wysyłał i odbierał wiadomość o maksymalnej długości 20 znaków.
"""

#!/usr/bin/env python

import socket, select
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 9006

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
                data = sock.recv(20)
                if data:
                    data = data[:20]
                    sock.send(data)
                    print("[%s] Sending back to client %s data: [\'%s\']... " % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), client_address, data))

            except:
                print("[%s] Client (%s) is offline" % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), client_address))
                sock.close()
                connected_clients_sockets.remove(sock)
                continue
server_socket.close()
