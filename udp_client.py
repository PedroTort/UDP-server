import socket
import struct
import zlib
import random

DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 5050
SEGMENT_SIZE = 1024
HEADER_SIZE = 13


def solicitar_configuracoes():
    server_ip = input(f"Digite o IP do servidor (padrao {DEFAULT_IP}): ").strip() or DEFAULT_IP
    port_input = input(f"Digite a porta do servidor (padrao {DEFAULT_PORT}): ").strip()
    server_port = int(port_input) if port_input else DEFAULT_PORT
    simulate_loss = input("Simular perda de pacotes? (s/N): ").strip().lower() == 's'
    simulate_interruption = input("Simular interrupcao do servidor durante a transferencia? (s/N): ").strip().lower() == 's'
    filename = input("Digite o nome do arquivo a ser requisitado: ").strip()
    return server_ip, server_port, filename, simulate_loss, simulate_interruption


def construir_mensagem(filename, simulate_interruption):
    message = f"GET {filename}"
    if simulate_interruption:
        message += " INTERROMPER"
    return message


def receber_arquivo(sock, server_ip, server_port, total_parts, simulate_loss):
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

            if simulate_loss and random.random() < 0.1:
                print(f"[SIMULACAO] Descartando pacote {sequence_number}")
                continue

            if received_checksum != calculated_checksum:
                print(f"[ERRO] Checksum incorreto no pacote {sequence_number}")
                continue

            if buffer[sequence_number] is None:
                buffer[sequence_number] = payload[:payload_size]
                received.add(sequence_number)
                print(f"[RECEBIDO {sequence_number}/{total_parts - 1}]")

            ack_message = f"ACK {sequence_number}"
            sock.sendto(ack_message.encode(), (server_ip, server_port))

        except socket.timeout:
            print("[TIMEOUT] Aguardando pacotes restantes...")
            break

    return buffer


def salvar_arquivo(buffer):
    if None not in buffer:
        print("[TODAS AS PARTES RECEBIDAS] Reconstruindo o arquivo...")
        full_data = b''.join(buffer)
        with open("arquivo_recebido.txt", "wb") as f:
            f.write(full_data)
        print("[ARQUIVO SALVO COMO] 'arquivo_recebido.txt'")
    else:
        print("[ERRO] Algumas partes estao faltando.")


def main():
    # solicitar configuracoes do usuario
    server_ip, server_port, filename, simulate_loss, simulate_interruption = solicitar_configuracoes()
    message = construir_mensagem(filename, simulate_interruption)

    # criar socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)
    sock.sendto(message.encode(), (server_ip, server_port))

    try:
        # aguardar resposta do servidor
        response, _ = sock.recvfrom(1024)
        response_str = response.decode()

        print("\n[RESPOSTA DO SERVIDOR]")
        print(response_str)

        # se tiver "ERRO", imprimir e encerrar
        if response_str.startswith("ERRO"):
            print("[ENCERRADO] O servidor retornou um erro.")
            return

        # se tiver "ok: enviando", receber o arquivo
        if "OK: Enviando" in response_str:
            total_parts = int(response_str.split()[-2])
            buffer = receber_arquivo(sock, server_ip, server_port, total_parts, simulate_loss)
            salvar_arquivo(buffer)

    except socket.timeout:
        print("[ERRO] Sem resposta do servidor.")


if __name__ == "__main__":
    main()
