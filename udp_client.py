import socket
import struct
import zlib

DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 5050
SEGMENT_SIZE = 1024
HEADER_SIZE = 13

server_ip = input(f"Digite o IP do servidor (padrão {DEFAULT_IP}): ").strip() or DEFAULT_IP
port_input = input(f"Digite a porta do servidor (padrão {DEFAULT_PORT}): ").strip()
server_port = int(port_input) if port_input else DEFAULT_PORT

mode = input("Escolha o modo (1 - Mensagem | 2 - Requisição de Arquivo): ").strip()

if mode == "1":
    content = input("Digite a mensagem a ser enviada: ").strip()
    message = content.encode()
elif mode == "2":
    filename = input("Digite o nome do arquivo a ser requisitado: ").strip()
    message = f"GET {filename}".encode()
else:
    print("Modo inválido. Encerrando.")
    exit()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(message, (server_ip, server_port))

response, _ = sock.recvfrom(1024)
print("\n[RESPOSTA DO SERVIDOR]")
print(response.decode())

if "OK: Enviando" in response.decode():
    total_parts = int(response.decode().split()[-2])
    buffer = [None] * total_parts
    parts_received = 0

    print(f"[RECEBENDO ARQUIVO em {total_parts} partes]")

    while parts_received < total_parts:
        packet, _ = sock.recvfrom(SEGMENT_SIZE)

        try:
            header = packet[:HEADER_SIZE]
            payload = packet[HEADER_SIZE:]

            sequence_number, is_last, payload_size, received_checksum = struct.unpack("!IBII", header)
            calculated_checksum = zlib.crc32(payload)

            if received_checksum != calculated_checksum:
                print(f"[ERRO] Falha de checksum na parte {sequence_number}")
                continue

            if buffer[sequence_number] is None:
                buffer[sequence_number] = payload[:payload_size]
                parts_received += 1
                print(f"[PARTE RECEBIDA {sequence_number}/{total_parts - 1}] OK")

        except Exception as e:
            print(f"[ERRO] Falha ao processar segmento: {e}")

    if None not in buffer:
        print("[TODAS AS PARTES RECEBIDAS] Reconstruindo o arquivo...")
        full_data = b''.join(buffer)

        with open("arquivo_recebido.txt", "wb") as f:
            f.write(full_data)

        print("[ARQUIVO SALVO COMO] 'arquivo_recebido.txt'")
    else:
        print("[ERRO] Algumas partes estão faltando.")
