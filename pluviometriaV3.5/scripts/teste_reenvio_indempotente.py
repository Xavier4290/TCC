import json
import socket

from app.config import HOST_SERVIDOR_PC, PORTA_SERVIDOR_PC, TIMEOUT_SOCKET_SEGUNDOS
from pc.repositorio_central import RepositorioCentralSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def enviar_payload(payload: dict) -> dict:
    """Envia um payload JSON ao servidor e retorna a resposta decodificada."""
    carga = json.dumps(payload, ensure_ascii=False).encode("utf-8")

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
        raise RuntimeError("O servidor não retornou resposta.")

    return json.loads(resposta.decode("utf-8"))


def main() -> None:
    """Valida que o mesmo lote pode ser reenviado sem duplicar a base central."""
    repositorio_central = RepositorioCentralSQLite()
    repositorio_central.inicializar_banco()
    repositorio_central.remover_todos_registros()

    lote = {
        "medicoes": [
            {
                "id": 9001,
                "data_hora": "2026-04-19 04:00:00",
                "pulsos": 2,
                "chuva_intervalo_mm": 0.50,
                "chuva_acumulada_mm": 0.50,
            },
            {
                "id": 9002,
                "data_hora": "2026-04-19 04:00:15",
                "pulsos": 3,
                "chuva_intervalo_mm": 0.75,
                "chuva_acumulada_mm": 1.25,
            },
            {
                "id": 9003,
                "data_hora": "2026-04-19 04:00:30",
                "pulsos": 1,
                "chuva_intervalo_mm": 0.25,
                "chuva_acumulada_mm": 1.50,
            },
        ]
    }

    imprimir_titulo("Primeiro envio do lote")
    resposta_1 = enviar_payload(lote)
    print(resposta_1)

    total_apos_primeiro = repositorio_central.contar_registros()
    print(f"Total no banco central após o primeiro envio: {total_apos_primeiro}")

    imprimir_titulo("Segundo envio do mesmo lote")
    resposta_2 = enviar_payload(lote)
    print(resposta_2)

    total_apos_segundo = repositorio_central.contar_registros()
    print(f"Total no banco central após o segundo envio: {total_apos_segundo}")

    imprimir_titulo("Resultado esperado")
    print("O total do banco central deve continuar 3 após o segundo envio.")
    print("Os IDs devem continuar sendo confirmados pelo servidor.")


if __name__ == "__main__":
    main()