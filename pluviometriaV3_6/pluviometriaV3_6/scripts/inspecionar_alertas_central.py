import argparse

from pc.repositorio_alertas_ciclo import RepositorioAlertasCicloSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def obter_argumentos() -> argparse.Namespace:
    """Lê os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Inspeciona os alertas com ciclo de vida persistidos no banco central do PC."
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=20,
        help="Quantidade máxima de alertas exibidos. Padrão: 20.",
    )

    return parser.parse_args()


def main() -> None:
    """Exibe resumo e alertas persistidos."""
    argumentos = obter_argumentos()

    if argumentos.limite <= 0:
        raise ValueError("O valor de --limite deve ser maior que zero.")

    repositorio = RepositorioAlertasCicloSQLite()
    repositorio.inicializar_banco()

    total = repositorio.contar_alertas()
    registros = repositorio.listar_todos(limite=argumentos.limite)

    imprimir_titulo("Resumo dos alertas centrais")
    print(f"Total de alertas persistidos: {total}")

    imprimir_titulo(f"Alertas centrais (até {argumentos.limite})")

    if not registros:
        print("Nenhum alerta encontrado.")
        return

    for registro in registros:
        print(
            f"id={registro['id']} | "
            f"status={registro['status_alerta']} | "
            f"nivel_atual={registro['nivel_alerta_atual']} | "
            f"nivel_maximo={registro['nivel_alerta_maximo']} | "
            f"primeira_medicao_origem={registro['primeira_medicao_origem']} | "
            f"ultima_medicao_origem={registro['ultima_medicao_origem']} | "
            f"atualizacoes={registro['quantidade_atualizacoes']} | "
            f"aberto_em={registro['aberto_em']} | "
            f"atualizado_em={registro['atualizado_em']} | "
            f"encerrado_em={registro['encerrado_em']}"
        )


if __name__ == "__main__":
    main()