import socket

hex_data = "45 00 00 4e f7 fa 40 00 38 06 9d 33 d4 b6 18 1b c0 a8 00 02 0b 54 b9 a6 fb f9 3c 57 c1 0a 06 c1 80 18 00 e3 ce 9c 00 00 01 01 08 0a 03 a6 eb 01 00 0b f8 e5 6e 65 74 77 6f 72 6b 20 70 72 6f 67 72 61 6d 6d 69 6e 67 20 69 73 20 66 75 6e"

data_bytes = bytes.fromhex(hex_data.replace(" ", ""))

# Nagłówek IP:
# Bajt 0:      wersja (górne 4 bity) + IHL (dolne 4 bity)
# Bajt 9:      protokół (6=TCP, 17=UDP)
# Bajty 12-15: źródłowy adres IP
# Bajty 16-19: docelowy adres IP

version    = data_bytes[0] >> 4
ihl        = (data_bytes[0] & 0x0F) * 4  # rozmiar nagłówka IP w bajtach
protocol   = data_bytes[9]
src_ip     = ".".join(str(b) for b in data_bytes[12:16])
dst_ip     = ".".join(str(b) for b in data_bytes[16:20])

print(f"Wersja IP     : {version}")
print(f"Nagłówek IP   : {ihl} bajtów")
print(f"Protokół      : {protocol} ({'TCP' if protocol == 6 else 'UDP'})")
print(f"Źródłowy IP   : {src_ip}")
print(f"Docelowy IP   : {dst_ip}")

transport = data_bytes[ihl:]

if protocol == 6:  # TCP
    src_port    = int.from_bytes(transport[0:2], 'big')
    dst_port    = int.from_bytes(transport[2:4], 'big')
    tcp_offset  = (transport[12] >> 4) * 4 
    data        = transport[tcp_offset:].decode('utf-8')
elif protocol == 17:  # UDP
    src_port = int.from_bytes(transport[0:2], 'big')
    dst_port = int.from_bytes(transport[2:4], 'big')
    data     = transport[8:].decode('utf-8')

print(f"Port źródłowy : {src_port}")
print(f"Port docelowy : {dst_port}")
print(f"Dane          : {data}")

# Wiadomość A
msgA = f"zad15odpA;ver;{version};srcip;{src_ip};dstip;{dst_ip};type;{protocol}"
# Wiadomość B
msgB = f"zad15odpB;srcport;{src_port};dstport;{dst_port};data;{data}"

print(f"\nWysyłam A: {msgA}")
print(f"Wysyłam B: {msgB}")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(5)

        s.sendto(msgA.encode('utf-8'), ("127.0.0.1", 2911))
        respA, _ = s.recvfrom(1024)
        print(f"Odpowiedź A: {respA.decode('utf-8')}")

        if respA.decode('utf-8') == "TAK":
            s.sendto(msgB.encode('utf-8'), ("127.0.0.1", 2911))
            respB, _ = s.recvfrom(1024)
            print(f"Odpowiedź B: {respB.decode('utf-8')}")
except Exception as e:
    print(f"Błąd: {e}")