import socket
import os
import zlib
import struct
import time
import random

UDP_IP = "127.0.0.1"
UDP_PORT = 5050
SEGMENT_SIZE = 1024
HEADER_SIZE = 13  # 4 (seq) + 1 (is_last) + 4 (payload_size) + 4 (checksum)
PAYLOAD_SIZE = SEGMENT_SIZE - HEADER_SIZE
TIMEOUT = 1.0
MAX_RETRIES = 5

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(TIMEOUT)

print(f"[SERVIDOR] Escutando em {UDP_IP}:{UDP_PORT}")

pacotes_enviados = {}
client_connected = False

while True:
    try:
        data, addr = sock.recvfrom(1024)
        message = data.decode(errors="ignore").strip()
        print(f"[REQUISIÇÃO de {addr}] {message}")

        if client_connected:
            error_msg = "ERRO: Servidor já ocupado."
            sock.sendto(error_msg.encode(), addr)
            print(f"[ERRO] Servidor já ocupado. Não é possível aceitar nova conexão de {addr}")
            continue
        
        if message.startswith("GET"):
            client_connected = True  # Marca que o servidor está ocupado com um cliente

            # Separa o comando GET do nome do arquivo e da palavra "INTERROMPER"
            parts = message.split()
            filename = parts[1] if len(parts) > 1 else None
            simulate_interruption = "INTERROMPER" in parts  # Verifica se "INTERROMPER" está presente

            if not filename:
                error_msg = "ERRO: Nome do arquivo não pode ser vazio."
                sock.sendto(error_msg.encode(), addr)
                print(f"[ERRO] {error_msg} para {addr}")
                client_connected = False
                continue

            if not os.path.isfile(filename):
                error_msg = f"ERRO: Arquivo '{filename}' não encontrado."
                sock.sendto(error_msg.encode(), addr)
                print(f"[ERRO] {error_msg} para {addr}")
                client_connected = False
                continue

            filesize = os.path.getsize(filename)
            total_parts = (filesize + PAYLOAD_SIZE - 1) // PAYLOAD_SIZE

            sock.sendto(f"OK: Enviando '{filename}' em {total_parts} partes".encode(), addr)
            pacotes_enviados[addr] = {}

            with open(filename, "rb") as f:
                seq = 0
                while seq < total_parts:
                    payload = f.read(PAYLOAD_SIZE)
                    is_last = 1 if seq == total_parts - 1 else 0
                    payload_size = len(payload)
                    checksum = zlib.crc32(payload)
                    header = struct.pack("!IBII", seq, is_last, payload_size, checksum)
                    packet = header + payload

                    retries = 0
                    while retries < MAX_RETRIES:
                        sock.sendto(packet, addr)
                        pacotes_enviados[addr][seq] = packet
                        print(f"[ENVIADO {seq}] {payload_size} bytes, aguardando ACK...")

                        # Simula interrupção do servidor se a opção for ativada
                        if simulate_interruption and random.random() < 0.1:  # 10% de chance
                            print(f"[SIMULAÇÃO] Interrupção do servidor. Pausando por 5 segundos.")
                            time.sleep(1)

                        try:
                            sock.settimeout(TIMEOUT)
                            ack_data, _ = sock.recvfrom(1024)
                            ack_msg = ack_data.decode().strip()

                            if ack_msg == f"ACK {seq}":
                                print(f"[ACK RECEBIDO] {seq}")
                                break
                            else:
                                print(f"[ACK INVÁLIDO] {ack_msg}")
                        except socket.timeout:
                            retries += 1
                            print(f"[TIMEOUT] Tentando reenviar {seq} ({retries}/{MAX_RETRIES})")

                    if retries >= MAX_RETRIES:
                        print(f"[FALHA] Pacote {seq} não confirmado após {MAX_RETRIES} tentativas.")
                        break

                    seq += 1

            client_connected = False  # Libera para o próximo cliente

        else:
            sock.sendto("ERRO: Comando não reconhecido.".encode(), addr)

    except socket.timeout:
        continue
