from pc.persistencia_central import PersistenciaCentralSQLite
from pc.repositorio_alertas import RepositorioAlertasSQLite
from pc.repositorio_analitico import RepositorioAnaliticoSQLite
from pc.repositorio_central import RepositorioCentralSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def main() -> None:
    """Valida a integração entre persistência bruta, análise e alertas no lado do PC."""
    repositorio_central = RepositorioCentralSQLite()
    repositorio_central.inicializar_banco()
    repositorio_central.remover_todos_registros()

    repositorio_analitico = RepositorioAnaliticoSQLite()
    repositorio_analitico.inicializar_banco()
    repositorio_analitico.remover_todas_analises()

    repositorio_alertas = RepositorioAlertasSQLite()
    repositorio_alertas.inicializar_banco()
    repositorio_alertas.remover_todos_alertas()

    persistencia = PersistenciaCentralSQLite(
        repositorio=repositorio_central,
        repositorio_analitico=repositorio_analitico,
        repositorio_alertas=repositorio_alertas,
    )

    lote_1 = [
        {
            "id": 6001,
            "data_hora": "2026-04-20 03:00:00",
            "pulsos": 0,
            "chuva_intervalo_mm": 0.00,
            "chuva_acumulada_mm": 0.00,
        },
        {
            "id": 6002,
            "data_hora": "2026-04-20 03:00:15",
            "pulsos": 1,
            "chuva_intervalo_mm": 0.25,
            "chuva_acumulada_mm": 0.25,
        },
        {
            "id": 6003,
            "data_hora": "2026-04-20 03:00:30",
            "pulsos": 2,
            "chuva_intervalo_mm": 0.50,
            "chuva_acumulada_mm": 0.75,
        },
    ]

    lote_2 = [
        {
            "id": 6004,
            "data_hora": "2026-04-20 03:00:45",
            "pulsos": 4,
            "chuva_intervalo_mm": 1.00,
            "chuva_acumulada_mm": 1.75,
        },
        {
            "id": 6005,
            "data_hora": "2026-04-20 03:01:00",
            "pulsos": 6,
            "chuva_intervalo_mm": 1.50,
            "chuva_acumulada_mm": 3.25,
        },
        {
            "id": 6006,
            "data_hora": "2026-04-20 03:01:15",
            "pulsos": 8,
            "chuva_intervalo_mm": 2.00,
            "chuva_acumulada_mm": 5.25,
        },
    ]

    imprimir_titulo("Processando lote 1")
    confirmados_1 = persistencia.processar_lote(lote_1)
    print(f"IDs confirmados no lote 1: {confirmados_1}")
    print(f"Total bruto: {repositorio_central.contar_registros()}")
    print(f"Total de análises: {repositorio_analitico.contar_analises()}")
    print(f"Total de alertas: {repositorio_alertas.contar_alertas()}")

    imprimir_titulo("Processando lote 2")
    confirmados_2 = persistencia.processar_lote(lote_2)
    print(f"IDs confirmados no lote 2: {confirmados_2}")
    print(f"Total bruto: {repositorio_central.contar_registros()}")
    print(f"Total de análises: {repositorio_analitico.contar_analises()}")
    print(f"Total de alertas: {repositorio_alertas.contar_alertas()}")

    imprimir_titulo("Listagem final de alertas")
    for alerta in repositorio_alertas.listar_todos(limite=20):
        print(
            f"id={alerta['id']} | "
            f"id_ultima_medicao_origem={alerta['id_ultima_medicao_origem']} | "
            f"nivel_alerta={alerta['nivel_alerta']} | "
            f"mensagem={alerta['mensagem_alerta']}"
        )


if __name__ == "__main__":
    main()