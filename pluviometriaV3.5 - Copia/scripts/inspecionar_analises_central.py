import argparse

from pc.repositorio_analitico import RepositorioAnaliticoSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def obter_argumentos() -> argparse.Namespace:
    """Lê os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Inspeciona as análises persistidas no banco central do PC."
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=20,
        help="Quantidade máxima de análises exibidas. Padrão: 20.",
    )

    return parser.parse_args()


def main() -> None:
    """Exibe resumo e análises persistidas."""
    argumentos = obter_argumentos()

    if argumentos.limite <= 0:
        raise ValueError("O valor de --limite deve ser maior que zero.")

    repositorio = RepositorioAnaliticoSQLite()
    repositorio.inicializar_banco()

    total = repositorio.contar_analises()
    registros = repositorio.listar_todas(limite=argumentos.limite)

    imprimir_titulo("Resumo das análises centrais")
    print(f"Total de análises persistidas: {total}")

    imprimir_titulo(f"Análises centrais (até {argumentos.limite})")

    if not registros:
        print("Nenhuma análise encontrada.")
        return

    for registro in registros:
        print(
            f"id={registro['id']} | "
            f"id_ultima_medicao_origem={registro['id_ultima_medicao_origem']} | "
            f"classificacao={registro['classificacao_chuva']} | "
            f"severidade={registro['severidade_operacional']} | "
            f"tendencia={registro['tendencia_final']} | "
            f"pre_alerta={registro['sinal_pre_alerta']} | "
            f"alerta={registro['alerta_recomendado']} | "
            f"confianca={registro['score_confianca']} | "
            f"analisado_em={registro['analisado_em']}"
        )


if __name__ == "__main__":
    main()