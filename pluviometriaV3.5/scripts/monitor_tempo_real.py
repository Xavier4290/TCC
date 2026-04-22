import argparse

from app.config import CAMINHO_BANCO_CENTRAL_PC
from pc.monitor_tempo_real import MonitorTempoRealPluviometria


def obter_argumentos() -> argparse.Namespace:
    """Lê os argumentos da linha de comando do monitor."""
    parser = argparse.ArgumentParser(
        description="Abre um monitor gráfico simplificado em tempo real do banco central."
    )

    parser.add_argument(
        "--limite-medicoes",
        type=int,
        default=30,
        help="Quantidade de medições exibidas. Padrão: 30.",
    )
    parser.add_argument(
        "--limite-analises",
        type=int,
        default=20,
        help="Quantidade de análises exibidas. Padrão: 20.",
    )
    parser.add_argument(
        "--limite-alertas",
        type=int,
        default=20,
        help="Quantidade de alertas exibidos. Padrão: 20.",
    )
    parser.add_argument(
        "--intervalo-ms",
        type=int,
        default=2000,
        help="Intervalo de atualização em milissegundos. Padrão: 2000.",
    )

    return parser.parse_args()


def main() -> None:
    """Inicializa e executa o monitor gráfico."""
    argumentos = obter_argumentos()

    monitor = MonitorTempoRealPluviometria(
        caminho_banco=CAMINHO_BANCO_CENTRAL_PC,
        limite_medicoes=argumentos.limite_medicoes,
        limite_analises=argumentos.limite_analises,
        limite_alertas=argumentos.limite_alertas,
        intervalo_atualizacao_ms=argumentos.intervalo_ms,
    )
    monitor.executar()


if __name__ == "__main__":
    main()