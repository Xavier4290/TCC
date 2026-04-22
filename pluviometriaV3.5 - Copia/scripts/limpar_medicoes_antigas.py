import argparse
from datetime import datetime, timedelta

from app.repositorio_medicoes import RepositorioMedicoesSQLite


FORMATO_DATA = "%Y-%m-%d %H:%M:%S"


def obter_argumentos() -> argparse.Namespace:
    """Lê os argumentos da linha de comando para limpeza por idade."""
    parser = argparse.ArgumentParser(
        description="Remove medições ENVIADO antigas do banco local."
    )

    parser.add_argument(
        "--antes-de",
        type=str,
        help="Remove medições ENVIADO com enviado_em anterior à data informada no formato YYYY-MM-DD HH:MM:SS.",
    )

    parser.add_argument(
        "--mais-antigas-que-horas",
        type=float,
        help="Remove medições ENVIADO com enviado_em mais antigo do que a quantidade de horas informada.",
    )

    return parser.parse_args()


def validar_argumentos(argumentos: argparse.Namespace) -> None:
    """Garante que exatamente um critério de tempo foi informado."""
    opcoes_ativas = sum(
        [
            argumentos.antes_de is not None,
            argumentos.mais_antigas_que_horas is not None,
        ]
    )

    if opcoes_ativas == 0:
        raise ValueError(
            "Informe um critério: --antes-de ou --mais-antigas-que-horas."
        )

    if opcoes_ativas > 1:
        raise ValueError(
            "Use apenas um critério por vez: --antes-de ou --mais-antigas-que-horas."
        )

    if argumentos.mais_antigas_que_horas is not None and argumentos.mais_antigas_que_horas <= 0:
        raise ValueError("O valor de --mais-antigas-que-horas deve ser maior que zero.")


def obter_data_limite(argumentos: argparse.Namespace) -> str:
    """Converte o critério recebido em uma data limite no formato padrão."""
    if argumentos.antes_de is not None:
        try:
            data = datetime.strptime(argumentos.antes_de.strip(), FORMATO_DATA)
        except ValueError as erro:
            raise ValueError(
                "A data informada em --antes-de deve estar no formato YYYY-MM-DD HH:MM:SS."
            ) from erro

        return data.strftime(FORMATO_DATA)

    agora = datetime.now()
    delta = timedelta(hours=argumentos.mais_antigas_que_horas)
    data_limite = agora - delta
    return data_limite.strftime(FORMATO_DATA)


def main() -> None:
    """Executa a limpeza de medições ENVIADO mais antigas que a data limite."""
    argumentos = obter_argumentos()
    validar_argumentos(argumentos)

    data_limite = obter_data_limite(argumentos)

    repositorio = RepositorioMedicoesSQLite()
    repositorio.inicializar_banco()

    removidos = repositorio.remover_medicoes_enviadas_mais_antigas_que(data_limite)

    print(f"Data limite usada: {data_limite}")
    print(f"Medições ENVIADO removidas: {removidos}")


if __name__ == "__main__":
    main()