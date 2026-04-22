import argparse

from app.repositorio_medicoes import RepositorioMedicoesSQLite


def obter_argumentos() -> argparse.Namespace:
    """Lê os argumentos de linha de comando para limpeza seletiva do banco."""
    parser = argparse.ArgumentParser(
        description="Remove medições do banco local de forma controlada."
    )

    parser.add_argument(
        "--enviadas",
        action="store_true",
        help="Remove apenas as medições com status ENVIADO.",
    )

    parser.add_argument(
        "--pendentes",
        action="store_true",
        help="Remove apenas as medições com status PENDENTE.",
    )

    parser.add_argument(
        "--todas",
        action="store_true",
        help="Remove todas as medições do banco local.",
    )

    return parser.parse_args()


def validar_argumentos(argumentos: argparse.Namespace) -> None:
    """Garante que exatamente uma estratégia de limpeza foi escolhida."""
    opcoes_ativas = sum(
        [
            argumentos.enviadas,
            argumentos.pendentes,
            argumentos.todas,
        ]
    )

    if opcoes_ativas == 0:
        raise ValueError(
            "Informe uma opção de limpeza: --enviadas, --pendentes ou --todas."
        )

    if opcoes_ativas > 1:
        raise ValueError(
            "Use apenas uma opção por vez: --enviadas, --pendentes ou --todas."
        )


def main() -> None:
    """Executa a limpeza seletiva conforme a opção escolhida."""
    argumentos = obter_argumentos()
    validar_argumentos(argumentos)

    repositorio = RepositorioMedicoesSQLite()
    repositorio.inicializar_banco()

    if argumentos.enviadas:
        removidos = repositorio.remover_medicoes_enviadas()
        print(f"Medições ENVIADO removidas: {removidos}")
        return

    if argumentos.pendentes:
        removidos = repositorio.remover_medicoes_pendentes()
        print(f"Medições PENDENTE removidas: {removidos}")
        return

    if argumentos.todas:
        removidos = repositorio.remover_todas_medicoes()
        print(f"Todas as medições removidas: {removidos}")
        return


if __name__ == "__main__":
    main()