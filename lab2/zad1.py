"""
Napisz program, ktory z serwera ntp.task.gda.pl pobierze aktualna
date i czas, a nastepnie wyswietli je na konsoli. Serwer dziala na
porcie 13.
"""

# Najpierw sprobowalam w ten sposob ale serwer nie odpowiadal:

# import socket

# serwer_address = ("ntp.task.gda.pl", 13)
# try:
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.settimeout(5)
#         s.connect(serwer_address)
#         data = s.recv(1024)
#         print("Data i czas z serwera ntp.task.gda.pl:", data.decode())
# except socket.timeout:
#     print("Serwer nie odpowiedzial w czasie 5 sekund.")
# except Exception as e:
#     print("Blad:", e)

import ntplib
from datetime import datetime
from zoneinfo import ZoneInfo

c = ntplib.NTPClient()
response = c.request('ntp.task.gda.pl', version=3)
dt = datetime.fromtimestamp(response.tx_time, tz=ZoneInfo("Europe/Warsaw"))
print("Data i czas:", dt.strftime("%Y-%m-%d %H:%M:%S"))