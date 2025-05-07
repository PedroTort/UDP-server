# Transferência de Arquivos via UDP

Este projeto simula uma transferência de arquivos usando o protocolo UDP, com verificação de integridade por checksum (CRC32), e inclui funcionalidades para simular perda de pacotes e interrupção do servidor.

## Requisitos

Este projeto utiliza apenas bibliotecas da **biblioteca padrão do Python**. Portanto, **não é necessário instalar dependências externas**.

Recomenda-se Python 3.8 ou superior.

## Estrutura do Projeto

- `cliente.py`: Código do cliente que solicita e recebe o arquivo.
- `servidor.py`: Código do servidor que envia o arquivo ao cliente.

## Como Executar

1. **Abra dois terminais**.

2. No **primeiro terminal**, inicie o servidor:

   python servidor.py

3. Em seguida, inicio o cliente:

  python cliente.py
