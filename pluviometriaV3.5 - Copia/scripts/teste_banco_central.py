from pc.persistencia_central import PersistenciaCentralSQLite
from pc.repositorio_central import RepositorioCentralSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def main() -> None:
    """Testa a persistência central do PC sem depender do servidor TCP."""
    repositorio = RepositorioCentralSQLite()
    repositorio.inicializar_banco()
    repositorio.remover_todos_registros()

    persistencia = PersistenciaCentralSQLite(repositorio)

    lote_teste = [
        {
            "id": 101,
            "data_hora": "2026-04-19 03:00:00",
            "pulsos": 2,
            "chuva_intervalo_mm": 0.50,
            "chuva_acumulada_mm": 0.50,
        },
        {
            "id": 102,
            "data_hora": "2026-04-19 03:00:15",
            "pulsos": 4,
            "chuva_intervalo_mm": 1.00,
            "chuva_acumulada_mm": 1.50,
        },
    ]

    imprimir_titulo("Processando lote de teste no banco central")
    ids_confirmados = persistencia.processar_lote(lote_teste)
    print(f"IDs confirmados: {ids_confirmados}")

    imprimir_titulo("Resumo após persistência")
    total = repositorio.contar_registros()
    print(f"Total de registros no banco central: {total}")

    imprimir_titulo("Listagem do banco central")
    registros = repositorio.listar_todas(limite=20)

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