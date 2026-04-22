import argparse

from app.repositorio_medicoes import RepositorioMedicoesSQLite


def formatar_medicao(medicao) -> str:
    """Converte uma medição persistida em uma linha legível para o terminal."""
    return (
        f"ID={medicao.id} | data_hora={medicao.data_hora} | "
        f"pulsos={medicao.pulsos} | "
        f"intervalo={medicao.chuva_intervalo_mm:.2f} mm | "
        f"acumulado={medicao.chuva_acumulada_mm:.2f} mm | "
        f"status={medicao.status_sync} | "
        f"tentativas={medicao.tentativas_envio} | "
        f"enviado_em={medicao.enviado_em} | "
        f"erro={medicao.ultimo_erro}"
    )


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def obter_argumentos() -> argparse.Namespace:
    """Lê os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Inspeciona o banco SQLite local de medições."
    )

    parser.add_argument(
        "--pendentes",
        action="store_true",
        help="Mostra apenas as medições pendentes.",
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=20,
        help="Quantidade máxima de registros exibidos. Padrão: 20.",
    )

    return parser.parse_args()


def main() -> None:
    """Exibe resumo e registros do banco local conforme os argumentos informados."""
    argumentos = obter_argumentos()

    if argumentos.limite <= 0:
        raise ValueError("O valor de --limite deve ser maior que zero.")

    repositorio = RepositorioMedicoesSQLite()

    todas = repositorio.listar_todas()
    pendentes = repositorio.buscar_pendentes(limite=max(len(todas), argumentos.limite))

    total_medicoes = len(todas)
    total_pendentes = sum(1 for medicao in todas if medicao.status_sync == "PENDENTE")
    total_enviadas = sum(1 for medicao in todas if medicao.status_sync == "ENVIADO")

    imprimir_titulo("Resumo do banco local")
    print(f"Total de medições: {total_medicoes}")
    print(f"Total pendentes: {total_pendentes}")
    print(f"Total enviadas: {total_enviadas}")

    if argumentos.pendentes:
        registros = pendentes[: argumentos.limite]
        titulo = f"Pendentes (até {argumentos.limite})"
    else:
        registros = todas[: argumentos.limite]
        titulo = f"Registros gerais (até {argumentos.limite})"

    imprimir_titulo(titulo)

    if not registros:
        print("Nenhum registro encontrado.")
        return

    for medicao in registros:
        print(formatar_medicao(medicao))


if __name__ == "__main__":
    main()