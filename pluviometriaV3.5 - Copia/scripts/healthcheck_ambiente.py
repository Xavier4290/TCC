import json
import socket

from app.config import (
    CAMINHO_BANCO_CENTRAL_PC,
    CAMINHO_BANCO_SQLITE,
    HOST_SERVIDOR_PC,
    MODO_EXECUCAO,
    PORTA_SERVIDOR_PC,
    TIMEOUT_SOCKET_SEGUNDOS,
)
from app.repositorio_medicoes import RepositorioMedicoesSQLite
from pc.repositorio_central import RepositorioCentralSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def verificar_banco_local() -> None:
    """Exibe o estado do banco SQLite local."""
    repositorio_local = RepositorioMedicoesSQLite()
    repositorio_local.inicializar_banco()

    total = repositorio_local.contar_medicoes()
    pendentes = repositorio_local.contar_pendentes()
    enviadas = total - pendentes

    print(f"Banco local: {CAMINHO_BANCO_SQLITE}")
    print(f"Total local: {total}")
    print(f"Pendentes locais: {pendentes}")
    print(f"Enviadas locais: {enviadas}")


def verificar_banco_central_localmente() -> None:
    """Exibe o estado do banco central diretamente pelo SQLite, sem depender do servidor."""
    repositorio_central = RepositorioCentralSQLite()
    repositorio_central.inicializar_banco()

    total = repositorio_central.contar_registros()

    print(f"Banco central (acesso direto): {CAMINHO_BANCO_CENTRAL_PC}")
    print(f"Total central direto: {total}")


def verificar_servidor() -> None:
    """Consulta o servidor do PC via socket para confirmar identidade e persistência ativa."""
    payload = {"tipo": "healthcheck"}
    carga = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    try:
        with socket.create_connection(
            (HOST_SERVIDOR_PC, PORTA_SERVIDOR_PC),
            timeout=TIMEOUT_SOCKET_SEGUNDOS,
        ) as cliente:
            cliente.settimeout(TIMEOUT_SOCKET_SEGUNDOS)
            cliente.sendall(carga)
            cliente.shutdown(socket.SHUT_WR)

            resposta = bytearray()

            while True:
                trecho = cliente.recv(4096)
                if not trecho:
                    break
                resposta.extend(trecho)

        if not resposta:
            print("Servidor remoto: sem resposta.")
            return

        dados = json.loads(resposta.decode("utf-8"))

        print(f"Servidor remoto: {HOST_SERVIDOR_PC}:{PORTA_SERVIDOR_PC}")
        print(f"Status remoto: {dados.get('status')}")
        print(f"Serviço remoto: {dados.get('servico')}")
        print(f"Persistência remota: {dados.get('persistencia')}")
        print(f"Banco central remoto: {dados.get('banco_central')}")
        print(f"Total central remoto: {dados.get('total_registros_central')}")
        print(f"Mensagem remota: {dados.get('mensagem')}")

    except OSError as erro:
        print(f"Servidor remoto: indisponível ({erro})")


def main() -> None:
    """Executa uma verificação resumida do ambiente local e do servidor do PC."""
    imprimir_titulo("Health check do ambiente")
    print(f"Modo de execução configurado: {MODO_EXECUCAO}")

    imprimir_titulo("Banco local")
    verificar_banco_local()

    imprimir_titulo("Banco central por acesso direto")
    verificar_banco_central_localmente()

    imprimir_titulo("Servidor do PC via health check")
    verificar_servidor()


if __name__ == "__main__":
    main()