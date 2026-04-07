import socket
import time

IP_PC = "192.168.10.1"
PORTA = 5000

while True:
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((IP_PC, PORTA))

        with open("/home/enzo/Desktop/dados_pluviometro.csv", "r") as arquivo:
            dados = arquivo.read()

        cliente.sendall(dados.encode())

        cliente.close()

        print("Dados enviados")

    except Exception as erro:
        print("Erro:", erro)

    time.sleep(60)