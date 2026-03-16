import socket

hex_data = "ed 74 0b 55 00 24 ef fd 70 72 6f 67 72 61 6d 6d 69 6e 67 20 69 6e 20 70 79 74 68 6f 6e 20 69 73 20 66 75 6e"

data_bytes = bytes.fromhex(hex_data.replace(" ", ""))

src_port = int.from_bytes(data_bytes[0:2], byteorder='big')
dst_port = int.from_bytes(data_bytes[2:4], byteorder='big')
data = data_bytes[8:].decode('utf-8')

print(f"Port zrodlowy: {src_port}")
print(f"Port docelowy: {dst_port}")
print(f"Dane ({len(data)} bajtow): {data}")

message = f"zad14odp;src;{src_port};dst;{dst_port};data;{data}"
print(f"Wiadomosc do wyslania: {message}")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(5)
        s.sendto(message.encode('utf-8'), ("127.0.0.1", 2910))
        response, _ = s.recvfrom(1024)
        print(f"Odpowiedz od serwera: {response.decode('utf-8')}")
except Exception as e:
    print(f"Wystapil blad: {e}")