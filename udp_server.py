#Retransmissão: Implementar lógica para reenviar segmentos específicos caso o cliente solicite (devido a perdas ou erros).
#Lidar com pedidos de arquivos nao existentes
import socket
import os
import zlib
import struct

UDP_IP = "127.0.0.1"
UDP_PORT = 5050
SEGMENT_SIZE = 1024
HEADER_SIZE = 13  # 4 (seq) + 1 (is_last) + 4 (payload_size) + 4 (checksum)
PAYLOAD_SIZE = SEGMENT_SIZE - HEADER_SIZE

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"[SERVIDOR] Escutando em {UDP_IP}:{UDP_PORT}")

while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode().strip()
    print(f"[REQUISIÇÃO de {addr}] {message}")

    if message.startswith("GET "):
        filename = message[4:].strip()

        if os.path.isfile(filename):
            filesize = os.path.getsize(filename)
            total_parts = (filesize + PAYLOAD_SIZE - 1) // PAYLOAD_SIZE

            sock.sendto(f"OK: Enviando '{filename}' em {total_parts} partes".encode(), addr)

            with open(filename, "rb") as f:
                seq = 0
                while True:
                    payload = f.read(PAYLOAD_SIZE)
                    if not payload:
                        break

                    is_last = 1 if seq == total_parts - 1 else 0
                    payload_size = len(payload)
                    checksum = zlib.crc32(payload)

                    # Empacotamento do cabeçalho
                    header = struct.pack("!IBII", seq, is_last, payload_size, checksum) #magia do python, tentar entender
                    packet = header + payload

                    sock.sendto(packet, addr)
                    print(f"[ENVIADO {seq}/{total_parts - 1}] {payload_size} bytes, checksum={checksum}")
                    seq += 1
        else:
            sock.sendto("ERRO: Arquivo não encontrado.".encode(), addr)
    else:
        print(f"[MENSAGEM] {message}")
        response = f"Mensagem recebida: '{message}'"
        sock.sendto(response.encode(), addr)


#header = struct.pack("!IBII", seq, is_last, payload_size, checksum)
# !  -> Define a ordem dos bytes como 'big-endian' (ordem de bytes mais significativa primeiro)
# I  -> Um inteiro de 4 bytes (32 bits), usado para armazenar o número de sequência (seq)
# B  -> Um inteiro de 1 byte (8 bits), usado para armazenar o valor de 'is_last' (se é o último segmento ou não)
# I  -> Um inteiro de 4 bytes (32 bits), usado para armazenar o tamanho do payload (payload_size)
# I  -> Um inteiro de 4 bytes (32 bits), usado para armazenar o checksum calculado para o payload
# =13
# O resultado é um cabeçalho de 13 bytes que contém:
# - Número de sequência (seq) (4 bytes)
# - Flag indicando se é o último pacote (is_last) (1 byte)
# - Tamanho do payload do pacote (payload_size) (4 bytes)
# - Valor do checksum para verificar a integridade dos dados (checksum) (4 bytes)
