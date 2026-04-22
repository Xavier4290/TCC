from pc.persistencia_central import PersistenciaCentralSQLite
from pc.repositorio_analitico import RepositorioAnaliticoSQLite
from pc.repositorio_central import RepositorioCentralSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def main() -> None:
    """Valida a integração entre persistência bruta e análise automática no lado do PC."""
    repositorio_central = RepositorioCentralSQLite()
    repositorio_central.inicializar_banco()
    repositorio_central.remover_todos_registros()

    repositorio_analitico = RepositorioAnaliticoSQLite()
    repositorio_analitico.inicializar_banco()
    repositorio_analitico.remover_todas_analises()

    persistencia = PersistenciaCentralSQLite(
        repositorio=repositorio_central,
        repositorio_analitico=repositorio_analitico,
    )

    lote_1 = [
        {
            "id": 4001,
            "data_hora": "2026-04-19 10:00:00",
            "pulsos": 0,
            "chuva_intervalo_mm": 0.00,
            "chuva_acumulada_mm": 0.00,
        },
        {
            "id": 4002,
            "data_hora": "2026-04-19 10:00:15",
            "pulsos": 1,
            "chuva_intervalo_mm": 0.25,
            "chuva_acumulada_mm": 0.25,
        },
        {
            "id": 4003,
            "data_hora": "2026-04-19 10:00:30",
            "pulsos": 2,
            "chuva_intervalo_mm": 0.50,
            "chuva_acumulada_mm": 0.75,
        },
    ]

    lote_2 = [
        {
            "id": 4004,
            "data_hora": "2026-04-19 10:00:45",
            "pulsos": 4,
            "chuva_intervalo_mm": 1.00,
            "chuva_acumulada_mm": 1.75,
        },
        {
            "id": 4005,
            "data_hora": "2026-04-19 10:01:00",
            "pulsos": 6,
            "chuva_intervalo_mm": 1.50,
            "chuva_acumulada_mm": 3.25,
        },
        {
            "id": 4006,
            "data_hora": "2026-04-19 10:01:15",
            "pulsos": 8,
            "chuva_intervalo_mm": 2.00,
            "chuva_acumulada_mm": 5.25,
        },
    ]

    imprimir_titulo("Processando lote 1")
    confirmados_1 = persistencia.processar_lote(lote_1)
    print(f"IDs confirmados no lote 1: {confirmados_1}")
    print(f"Total de medições brutas: {repositorio_central.contar_registros()}")
    print(f"Total de análises: {repositorio_analitico.contar_analises()}")

    imprimir_titulo("Processando lote 2")
    confirmados_2 = persistencia.processar_lote(lote_2)
    print(f"IDs confirmados no lote 2: {confirmados_2}")
    print(f"Total de medições brutas: {repositorio_central.contar_registros()}")
    print(f"Total de análises: {repositorio_analitico.contar_analises()}")

    imprimir_titulo("Listagem final das análises")
    registros = repositorio_analitico.listar_todas(limite=20)
    for registro in registros:
        print(
            f"id={registro['id']} | "
            f"id_ultima_medicao_origem={registro['id_ultima_medicao_origem']} | "
            f"classificacao={registro['classificacao_chuva']} | "
            f"severidade={registro['severidade_operacional']} | "
            f"alerta={registro['alerta_recomendado']} | "
            f"confianca={registro['score_confianca']}"
        )


if __name__ == "__main__":
    main()