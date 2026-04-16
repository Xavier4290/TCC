import json
import socket
from typing import Dict, List

from app.config import PORTA_SERVIDOR_PC
from .persistencia_central import PersistenciaCentralSimulada


HOST = "0.0.0.0"
PORTA = PORTA_SERVIDOR_PC


def receber_texto_completo(conexao: socket.socket) -> str:
    """Lê todos os bytes enviados pelo cliente até o encerramento da escrita."""
    dados = bytearray()

    while True:
        trecho = conexao.recv(4096)
        if not trecho:
            break
        dados.extend(trecho)

    return dados.decode("utf-8")


def montar_resposta(status: str, ids_recebidos: List[int], mensagem: str) -> bytes:
    """Monta o JSON de resposta enviado ao cliente."""
    resposta = {
        "status": status,
        "ids_recebidos": ids_recebidos,
        "mensagem": mensagem,
    }
    return json.dumps(resposta, ensure_ascii=False).encode("utf-8")


def processar_payload(texto_recebido: str, persistencia: PersistenciaCentralSimulada) -> Dict[str, object]:
    """Valida o JSON recebido e repassa os registros para a persistência central simulada."""
    try:
        payload = json.loads(texto_recebido)
    except json.JSONDecodeError as erro:
        return {
            "status": "erro",
            "ids_recebidos": [],
            "mensagem": f"JSON inválido: {erro}",
        }

    medicoes = payload.get("medicoes")

    if not isinstance(medicoes, list):
        return {
            "status": "erro",
            "ids_recebidos": [],
            "mensagem": "O campo medicoes precisa ser uma lista.",
        }

    # Simulação temporária de confirmação parcial:
    # o servidor aceita apenas os 3 primeiros registros do lote (trocar variável medicoes para medicos_parciais)
    medicoes_parciais = medicoes[:3]
    ids_confirmados = persistencia.processar_lote(medicoes)

    if len(ids_confirmados) == len(medicoes):
        status = "ok"
        mensagem = f"Lote aceito com {len(ids_confirmados)} registro(s)."
    elif len(ids_confirmados) > 0:
        status = "parcial"
        mensagem = (
            f"Lote parcialmente aceito. "
            f"Confirmados: {len(ids_confirmados)} de {len(medicoes)}."
        )
    else:
        status = "erro"
        mensagem = "Nenhum registro do lote foi aceito."

    return {
        "status": status,
        "ids_recebidos": ids_confirmados,
        "mensagem": mensagem,
    }


def iniciar_servidor() -> None:
    """Inicia o servidor TCP e processa conexões sequenciais até interrupção manual."""
    persistencia = PersistenciaCentralSimulada()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PORTA))
        servidor.listen()

        print(f"Servidor aguardando conexões em {HOST}:{PORTA}")

        try:
            while True:
                conexao, endereco = servidor.accept()

                with conexao:
                    print(f"\nConexão recebida de {endereco}")

                    texto_recebido = receber_texto_completo(conexao)
                    resposta = processar_payload(texto_recebido, persistencia)

                    print(
                        f"Status: {resposta['status']} | "
                        f"IDs confirmados: {resposta['ids_recebidos']} | "
                        f"Mensagem: {resposta['mensagem']}"
                    )

                    conexao.sendall(
                        montar_resposta(
                            status=resposta["status"],
                            ids_recebidos=resposta["ids_recebidos"],
                            mensagem=resposta["mensagem"],
                        )
                    )

        except KeyboardInterrupt:
            print("\nServidor encerrado manualmente.")


if __name__ == "__main__":
    iniciar_servidor()