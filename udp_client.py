import socket
import struct
import zlib
import random

DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 5050
SEGMENT_SIZE = 1024
HEADER_SIZE = 13

server_ip = input(f"Digite o IP do servidor (padrão {DEFAULT_IP}): ").strip() or DEFAULT_IP
port_input = input(f"Digite a porta do servidor (padrão {DEFAULT_PORT}): ").strip()
server_port = int(port_input) if port_input else DEFAULT_PORT

simulate_loss = input("Simular perda de pacotes? (s/N): ").strip().lower() == 's'

filename = input("Digite o nome do arquivo a ser requisitado: ").strip()
message = f"GET {filename}".encode()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5.0)
sock.sendto(message, (server_ip, server_port))

try:
    response, _ = sock.recvfrom(1024)
    response_str = response.decode()

    print("\n[RESPOSTA DO SERVIDOR]")
    print(response_str)

    if response_str.startswith("ERRO"):
        print("[ENCERRADO] O servidor retornou um erro.")
        exit()

    if "OK: Enviando" in response_str:
        total_parts = int(response_str.split()[-2])
        buffer = [None] * total_parts
        received = set()

        print(f"[RECEBENDO ARQUIVO em {total_parts} partes]")

        while len(received) < total_parts:
            try:
                packet, _ = sock.recvfrom(SEGMENT_SIZE)
                header = packet[:HEADER_SIZE]
                payload = packet[HEADER_SIZE:]

                sequence_number, is_last, payload_size, received_checksum = struct.unpack("!IBII", header)
                calculated_checksum = zlib.crc32(payload)

                # Simula perda
                if simulate_loss and random.random() < 0.1:
                    print(f"[SIMULAÇÃO] Descartando pacote {sequence_number}")
                    continue

                if received_checksum != calculated_checksum:
                    print(f"[ERRO] Checksum incorreto no pacote {sequence_number}")
                    continue

                if buffer[sequence_number] is None:
                    buffer[sequence_number] = payload[:payload_size]
                    received.add(sequence_number)
                    print(f"[RECEBIDO {sequence_number}/{total_parts - 1}]")

                # Envia ACK
                ack_message = f"ACK {sequence_number}"
                sock.sendto(ack_message.encode(), (server_ip, server_port))

            except socket.timeout:
                print("[TIMEOUT] Aguardando pacotes restantes...")

        if None not in buffer:
            print("[TODAS AS PARTES RECEBIDAS] Reconstruindo o arquivo...")
            full_data = b''.join(buffer)

            with open("arquivo_recebido.txt", "wb") as f:
                f.write(full_data)

            print("[ARQUIVO SALVO COMO] 'arquivo_recebido.txt'")
        else:
            print("[ERRO] Algumas partes estão faltando.")

except socket.timeout:
    print("[ERRO] Sem resposta do servidor.")
