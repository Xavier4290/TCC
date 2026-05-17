from pc.persistencia_central import PersistenciaCentralSQLite
from pc.repositorio_alertas_ciclo import RepositorioAlertasCicloSQLite
from pc.repositorio_analitico import RepositorioAnaliticoSQLite
from pc.repositorio_central import RepositorioCentralSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def main() -> None:
    """Valida a integração entre persistência bruta, análise e ciclo de vida dos alertas."""
    repositorio_central = RepositorioCentralSQLite()
    repositorio_central.inicializar_banco()
    repositorio_central.remover_todos_registros()

    repositorio_analitico = RepositorioAnaliticoSQLite()
    repositorio_analitico.inicializar_banco()
    repositorio_analitico.remover_todas_analises()

    repositorio_alertas = RepositorioAlertasCicloSQLite()
    repositorio_alertas.inicializar_banco()
    repositorio_alertas.remover_todos_alertas()

    persistencia = PersistenciaCentralSQLite(
        repositorio=repositorio_central,
        repositorio_analitico=repositorio_analitico,
        repositorio_alertas_ciclo=repositorio_alertas,
    )

    lote_1 = [
        {
            "id": 8001,
            "data_hora": "2026-04-20 05:00:00",
            "pulsos": 0,
            "chuva_intervalo_mm": 0.00,
            "chuva_acumulada_mm": 0.00,
        },
        {
            "id": 8002,
            "data_hora": "2026-04-20 05:00:15",
            "pulsos": 1,
            "chuva_intervalo_mm": 0.25,
            "chuva_acumulada_mm": 0.25,
        },
        {
            "id": 8003,
            "data_hora": "2026-04-20 05:00:30",
            "pulsos": 2,
            "chuva_intervalo_mm": 0.50,
            "chuva_acumulada_mm": 0.75,
        },
    ]

    lote_2 = [
        {
            "id": 8004,
            "data_hora": "2026-04-20 05:00:45",
            "pulsos": 4,
            "chuva_intervalo_mm": 1.00,
            "chuva_acumulada_mm": 1.75,
        },
        {
            "id": 8005,
            "data_hora": "2026-04-20 05:01:00",
            "pulsos": 6,
            "chuva_intervalo_mm": 1.50,
            "chuva_acumulada_mm": 3.25,
        },
        {
            "id": 8006,
            "data_hora": "2026-04-20 05:01:15",
            "pulsos": 8,
            "chuva_intervalo_mm": 2.00,
            "chuva_acumulada_mm": 5.25,
        },
    ]

    lote_3 = [
        {
            "id": 8007,
            "data_hora": "2026-04-20 05:01:30",
            "pulsos": 5,
            "chuva_intervalo_mm": 1.25,
            "chuva_acumulada_mm": 6.50,
        },
        {
            "id": 8008,
            "data_hora": "2026-04-20 05:01:45",
            "pulsos": 4,
            "chuva_intervalo_mm": 1.00,
            "chuva_acumulada_mm": 7.50,
        },
        {
            "id": 8009,
            "data_hora": "2026-04-20 05:02:00",
            "pulsos": 3,
            "chuva_intervalo_mm": 0.75,
            "chuva_acumulada_mm": 8.25,
        },
    ]

    lote_4 = [
        {
            "id": 8010,
            "data_hora": "2026-04-20 05:02:15",
            "pulsos": 0,
            "chuva_intervalo_mm": 0.00,
            "chuva_acumulada_mm": 8.25,
        },
        {
            "id": 8011,
            "data_hora": "2026-04-20 05:02:30",
            "pulsos": 0,
            "chuva_intervalo_mm": 0.00,
            "chuva_acumulada_mm": 8.25,
        },
        {
            "id": 8012,
            "data_hora": "2026-04-20 05:02:45",
            "pulsos": 0,
            "chuva_intervalo_mm": 0.00,
            "chuva_acumulada_mm": 8.25,
        },
    ]

    lotes = [
        ("lote_1", lote_1),
        ("lote_2", lote_2),
        ("lote_3", lote_3),
        ("lote_4", lote_4),
    ]

    for nome, lote in lotes:
        imprimir_titulo(f"Processando {nome}")
        confirmados = persistencia.processar_lote(lote)
        print(f"IDs confirmados: {confirmados}")
        print(f"Total bruto: {repositorio_central.contar_registros()}")
        print(f"Total de análises: {repositorio_analitico.contar_analises()}")
        print(f"Total de alertas: {repositorio_alertas.contar_alertas()}")

    imprimir_titulo("Resumo final dos alertas com ciclo")
    for alerta in repositorio_alertas.listar_todos(limite=20):
        print(
            f"id={alerta['id']} | "
            f"status={alerta['status_alerta']} | "
            f"nivel_atual={alerta['nivel_alerta_atual']} | "
            f"nivel_maximo={alerta['nivel_alerta_maximo']} | "
            f"primeira_medicao_origem={alerta['primeira_medicao_origem']} | "
            f"ultima_medicao_origem={alerta['ultima_medicao_origem']} | "
            f"atualizacoes={alerta['quantidade_atualizacoes']} | "
            f"encerrado_em={alerta['encerrado_em']}"
        )


if __name__ == "__main__":
    main()