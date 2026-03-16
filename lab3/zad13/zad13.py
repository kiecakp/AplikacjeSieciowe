import socket

hex_data = "0b 54 89 8b 1f 9a 18 ec bb b1 64 f2 80 18 00 e3 67 71 00 00 01 01 08 0a 02 c1 a4 ee 00 1a 4c ee 68 65 6c 6c 6f 20 3a 29"

# konwersja hex na bajty
byte_data = bytes.fromhex(hex_data.replace(" ", ""))

# struktura naglowka TCP:
# bajty 0-1: port zrodlowy
# bajtu 2-3: port docelowy
# bajty 4-7: sekwencja
# bajty 8-11: potwierdzenie
# bajt 12: rozmiar naglowka (w 32-bitowych slowach)
# bajty 13-19: flagi i inne pola naglowka
# bajty 20+: opcje i dane

src_port = int.from_bytes(byte_data[0:2], byteorder='big')
dst_port = int.from_bytes(byte_data[2:4], byteorder='big')
data_offset = (byte_data[12] >> 4) * 4  # w bajtach
data = byte_data[data_offset:]

print(f"Port zrodlowy: {src_port}")
print(f"Port docelowy: {dst_port}")
print(f"Data offset   : {data_offset} bajtów")
print(f"Dane ({len(data)} bajtów): {data}")
print(f"Dane jako tekst: {data.decode('utf-8')}")

message = f"zad13odp;src;{src_port};dst;{dst_port};data;{data.decode('utf-8')}"
print(f"Wiadomosc do wyslania: {message}")

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(5)
        s.sendto(message.encode('utf-8'), ("127.0.0.1", 2909))
        response, _ = s.recvfrom(1024)
        print(f"Odpowiedz od serwera: {response.decode('utf-8')}")
except Exception as e:
    print(f"Wystapil blad: {e}")