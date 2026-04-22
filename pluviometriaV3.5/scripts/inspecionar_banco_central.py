import argparse

from pc.repositorio_central import RepositorioCentralSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def obter_argumentos() -> argparse.Namespace:
    """Lê os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Inspeciona o banco central SQLite do lado do PC."
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=20,
        help="Quantidade máxima de registros exibidos. Padrão: 20.",
    )

    return parser.parse_args()


def main() -> None:
    """Exibe resumo e registros persistidos na base central."""
    argumentos = obter_argumentos()

    if argumentos.limite <= 0:
        raise ValueError("O valor de --limite deve ser maior que zero.")

    repositorio = RepositorioCentralSQLite()
    repositorio.inicializar_banco()

    total = repositorio.contar_registros()
    registros = repositorio.listar_todas(limite=argumentos.limite)

    imprimir_titulo("Resumo do banco central")
    print(f"Total de registros persistidos: {total}")

    imprimir_titulo(f"Registros centrais (até {argumentos.limite})")

    if not registros:
        print("Nenhum registro encontrado.")
        return

    for registro in registros:
        print(
            f"id_central={registro['id']} | "
            f"id_origem={registro['id_origem']} | "
            f"data_hora={registro['data_hora']} | "
            f"pulsos={registro['pulsos']} | "
            f"intervalo={float(registro['chuva_intervalo_mm']):.2f} mm | "
            f"acumulado={float(registro['chuva_acumulada_mm']):.2f} mm | "
            f"recebido_em={registro['recebido_em']}"
        )


if __name__ == "__main__":
    main()