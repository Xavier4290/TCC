import json
import socket
from typing import Dict, List

from app.config import CAMINHO_BANCO_CENTRAL_PC, PORTA_SERVIDOR_PC
from .persistencia_central import PersistenciaCentralSQLite


HOST = "0.0.0.0"
PORTA = PORTA_SERVIDOR_PC
NOME_SERVICO = "pluviometria_servidor_pc"
TIPO_PERSISTENCIA = "sqlite"


def receber_texto_completo(conexao: socket.socket) -> str:
    """Lê todos os bytes enviados pelo cliente até o encerramento da escrita."""
    dados = bytearray()

    while True:
        trecho = conexao.recv(4096)
        if not trecho:
            break
        dados.extend(trecho)

    return dados.decode("utf-8")


def montar_resposta(status: str, ids_recebidos: List[int], mensagem: str, extras: Dict[str, object] | None = None) -> bytes:
    """Monta o JSON de resposta enviado ao cliente."""
    resposta = {
        "status": status,
        "ids_recebidos": ids_recebidos,
        "mensagem": mensagem,
    }

    if extras:
        resposta.update(extras)

    return json.dumps(resposta, ensure_ascii=False).encode("utf-8")


def processar_payload(texto_recebido: str, persistencia: PersistenciaCentralSQLite) -> Dict[str, object]:
    """Valida o JSON recebido e repassa os registros para a persistência central."""
    try:
        payload = json.loads(texto_recebido)
    except json.JSONDecodeError as erro:
        return {
            "status": "erro",
            "ids_recebidos": [],
            "mensagem": f"JSON inválido: {erro}",
        }

    tipo_requisicao = payload.get("tipo")

    if tipo_requisicao == "healthcheck":
        total_registros = persistencia.repositorio.contar_registros()
        return {
            "status": "ok",
            "ids_recebidos": [],
            "mensagem": "Health check concluído com sucesso.",
            "servico": NOME_SERVICO,
            "persistencia": TIPO_PERSISTENCIA,
            "banco_central": str(CAMINHO_BANCO_CENTRAL_PC),
            "total_registros_central": total_registros,
        }

    medicoes = payload.get("medicoes")

    if not isinstance(medicoes, list):
        return {
            "status": "erro",
            "ids_recebidos": [],
            "mensagem": "O campo medicoes precisa ser uma lista.",
        }

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
    persistencia = PersistenciaCentralSQLite()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PORTA))
        servidor.listen()

        print(f"Servidor aguardando conexões em {HOST}:{PORTA}")
        print(f"Serviço: {NOME_SERVICO}")
        print(f"Persistência central ativa: {TIPO_PERSISTENCIA}")
        print(f"Base central em uso: {CAMINHO_BANCO_CENTRAL_PC}")

        try:
            while True:
                conexao, endereco = servidor.accept()

                with conexao:
                    print(f"\nConexão recebida de {endereco}")

                    texto_recebido = receber_texto_completo(conexao)
                    resposta = processar_payload(texto_recebido, persistencia)

                    print(
                        f"Status: {resposta['status']} | "
                        f"IDs confirmados: {resposta.get('ids_recebidos', [])} | "
                        f"Mensagem: {resposta['mensagem']}"
                    )

                    extras = {
                        chave: valor
                        for chave, valor in resposta.items()
                        if chave not in {"status", "ids_recebidos", "mensagem"}
                    }

                    conexao.sendall(
                        montar_resposta(
                            status=resposta["status"],
                            ids_recebidos=resposta.get("ids_recebidos", []),
                            mensagem=resposta["mensagem"],
                            extras=extras,
                        )
                    )

        except KeyboardInterrupt:
            print("\nServidor encerrado manualmente.")


if __name__ == "__main__":
    iniciar_servidor()