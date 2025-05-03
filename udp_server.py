import socket
import os
import zlib
import struct
import time
import random

# Constantes
UDP_IP = "127.0.0.1"
UDP_PORT = 5050
SEGMENT_SIZE = 1024
HEADER_SIZE = 13  # 4 (seq) + 1 (is_last) + 4 (payload_size) + 4 (checksum)
PAYLOAD_SIZE = SEGMENT_SIZE - HEADER_SIZE
TIMEOUT = 1.0
MAX_RETRIES = 5

# Estado global
pacotes_enviados = {}

# Cria o socket UDP
def criar_socket():
    # ipv4 e UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(TIMEOUT)
    return sock

# Envia uma mensagem para o cliente
def enviar_mensagem(sock, msg, addr):
    sock.sendto(msg.encode(), addr)

# Prepara o pacote para envio
def preparar_pacote(seq, total_parts, payload):
    is_last = 1 if seq == total_parts - 1 else 0
    payload_size = len(payload)
    checksum = zlib.crc32(payload)
    header = struct.pack("!IBII", seq, is_last, payload_size, checksum)
    return header + payload


def enviar_arquivo(sock, addr, filename, simulate_interruption):

    if not filename:
        enviar_mensagem(sock, "ERRO: Nome do arquivo não pode ser vazio.", addr)
        return

    if not os.path.isfile(filename):
        enviar_mensagem(sock, f"ERRO: Arquivo '{filename}' não encontrado.", addr)
        return

    filesize = os.path.getsize(filename)
    total_parts = (filesize + PAYLOAD_SIZE - 1) // PAYLOAD_SIZE
    enviar_mensagem(sock, f"OK: Enviando '{filename}' em {total_parts} partes", addr)

    pacotes_enviados[addr] = {}

    with open(filename, "rb") as f:
        seq = 0
        while seq < total_parts:
            payload = f.read(PAYLOAD_SIZE)
            packet = preparar_pacote(seq, total_parts, payload)
            retries = 0

            while retries < MAX_RETRIES:
                sock.sendto(packet, addr)
                pacotes_enviados[addr][seq] = packet
                print(f"[ENVIADO {seq}] {len(payload)} bytes | Checksum: {zlib.crc32(payload)} | Aguardando ACK...")

                if simulate_interruption and random.random() < 0.1:
                    print(f"[SIMULAÇÃO] Interrupção do servidor. Pausando por 1 segundos.")
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



def processar_requisicao(sock, data, addr):
    message = data.decode(errors="ignore").strip()
    print(f"[REQUISIÇÃO de {addr}] {message}")

    if message.startswith("GET"):
        parts = message.split()
        filename = parts[1] if len(parts) > 1 else None
        simulate_interruption = "INTERROMPER" in parts
        enviar_arquivo(sock, addr, filename, simulate_interruption)
    else:
        enviar_mensagem(sock, "ERRO: Comando não reconhecido.", addr)


def main():
    print(f"[SERVIDOR] Escutando em {UDP_IP}:{UDP_PORT}")
    sock = criar_socket()

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            processar_requisicao(sock, data, addr)
        except socket.timeout:
            continue


if __name__ == "__main__":
    main()
