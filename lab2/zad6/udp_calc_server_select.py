#!/usr/bin/env python

import socket
import sys
from time import gmtime, strftime

HOST = '127.0.0.1'
PORT = 2902

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    sock.bind((HOST, PORT))
except socket.error as msg:
    print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()

print("[%s] UDP Calc Server is waiting for incoming connections ... " % strftime("%Y-%m-%d %H:%M:%S", gmtime()))

try:
    while True:

        data1, address = sock.recvfrom(4096)
        op, address = sock.recvfrom(4096)
        data2, address = sock.recvfrom(4096)

        if data1 and data2 and op:

            op = op.decode().strip()

            print("[%s] Got from client %s ... : %s %s %s" % (strftime("%Y-%m-%d %H:%M:%S", gmtime()), str(address), data1, op, data2))

            try :

                n1 = float(data1)
                n2 = float(data2)

                if op == '+':
                    result = n1 + n2
                elif op == '-':
                    result = n1 - n2  # fix: było +
                elif op == '*':
                    result = n1 * n2  # fix: było +
                elif op == '/':
                    result = n1 / n2  # fix: było +
                else:
                    result = "Bad operator. I support only +, -, *, /"

                sock.sendto(str(result).encode(), address)

            except ValueError as e:
                result = "%s" % e
                sent = sock.sendto(str(result), address)

            except:
                result = "Error"
                sent = sock.sendto(str(result), address)
finally:

    sock.close()
