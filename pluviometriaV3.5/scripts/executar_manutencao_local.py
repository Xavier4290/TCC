import argparse
from datetime import datetime, timedelta

from app.config import RETENCAO_LOCAL_ENVIADOS_HORAS
from app.repositorio_medicoes import RepositorioMedicoesSQLite


FORMATO_DATA = "%Y-%m-%d %H:%M:%S"


def obter_argumentos() -> argparse.Namespace:
    """Lê os argumentos da linha de comando para a manutenção local."""
    parser = argparse.ArgumentParser(
        description="Executa manutenção local no banco principal, removendo ENVIADO antigos."
    )

    parser.add_argument(
        "--retencao-horas",
        type=float,
        default=RETENCAO_LOCAL_ENVIADOS_HORAS,
        help=(
            "Quantidade de horas de retenção para registros ENVIADO. "
            f"Padrão: {RETENCAO_LOCAL_ENVIADOS_HORAS}."
        ),
    )

    parser.add_argument(
        "--executar",
        action="store_true",
        help="Executa a remoção real. Sem esta flag, o script apenas simula.",
    )

    return parser.parse_args()


def validar_argumentos(argumentos: argparse.Namespace) -> None:
    """Valida os parâmetros básicos recebidos."""
    if argumentos.retencao_horas <= 0:
        raise ValueError("O valor de --retencao-horas deve ser maior que zero.")


def calcular_data_limite(retencao_horas: float) -> str:
    """Calcula a data limite da política de retenção."""
    agora = datetime.now()
    data_limite = agora - timedelta(hours=retencao_horas)
    return data_limite.strftime(FORMATO_DATA)


def main() -> None:
    """Executa ou simula a manutenção local do banco principal."""
    argumentos = obter_argumentos()
    validar_argumentos(argumentos)

    repositorio = RepositorioMedicoesSQLite()
    repositorio.inicializar_banco()

    data_limite = calcular_data_limite(argumentos.retencao_horas)
    total_candidatos = repositorio.contar_medicoes_enviadas_mais_antigas_que(data_limite)

    print("Manutenção local do banco principal")
    print(f"Retenção configurada: {argumentos.retencao_horas} hora(s)")
    print(f"Data limite calculada: {data_limite}")
    print(f"Registros ENVIADO candidatos à remoção: {total_candidatos}")

    if not argumentos.executar:
        print("\nModo simulação: nenhuma remoção foi realizada.")
        print("Use --executar para aplicar a manutenção de verdade.")
        return

    removidos = repositorio.remover_medicoes_enviadas_mais_antigas_que(data_limite)

    print("\nManutenção executada com sucesso.")
    print(f"Registros removidos: {removidos}")


if __name__ == "__main__":
    main()