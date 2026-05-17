from pathlib import Path

from app.config import DATA_DIR
from pc.analisador_evento import analisar_evento_chuva
from pc.repositorio_analitico import RepositorioAnaliticoSQLite
from pc.repositorio_central import RepositorioCentralSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def preparar_banco_teste(caminho_banco: Path) -> None:
    """Remove o banco de teste anterior para garantir execução limpa."""
    caminho_banco.parent.mkdir(parents=True, exist_ok=True)

    if caminho_banco.exists():
        caminho_banco.unlink()


def inserir_medicoes_centro(repositorio_central: RepositorioCentralSQLite) -> None:
    """Insere medições brutas no banco central de teste."""
    medicoes = [
        {
            "id": 3001,
            "data_hora": "2026-04-19 09:00:00",
            "pulsos": 0,
            "chuva_intervalo_mm": 0.00,
            "chuva_acumulada_mm": 0.00,
        },
        {
            "id": 3002,
            "data_hora": "2026-04-19 09:00:15",
            "pulsos": 1,
            "chuva_intervalo_mm": 0.25,
            "chuva_acumulada_mm": 0.25,
        },
        {
            "id": 3003,
            "data_hora": "2026-04-19 09:00:30",
            "pulsos": 2,
            "chuva_intervalo_mm": 0.50,
            "chuva_acumulada_mm": 0.75,
        },
        {
            "id": 3004,
            "data_hora": "2026-04-19 09:00:45",
            "pulsos": 4,
            "chuva_intervalo_mm": 1.00,
            "chuva_acumulada_mm": 1.75,
        },
        {
            "id": 3005,
            "data_hora": "2026-04-19 09:01:00",
            "pulsos": 6,
            "chuva_intervalo_mm": 1.50,
            "chuva_acumulada_mm": 3.25,
        },
        {
            "id": 3006,
            "data_hora": "2026-04-19 09:01:15",
            "pulsos": 8,
            "chuva_intervalo_mm": 2.00,
            "chuva_acumulada_mm": 5.25,
        },
    ]

    for medicao in medicoes:
        repositorio_central.inserir_ou_confirmar_medicao(medicao)


def main() -> None:
    """Valida a persistência da camada analítica em banco SQLite separado."""
    caminho_banco_teste = DATA_DIR / "teste_persistencia_analitica.db"
    preparar_banco_teste(caminho_banco_teste)

    repositorio_central = RepositorioCentralSQLite(caminho_banco_teste)
    repositorio_central.inicializar_banco()

    repositorio_analitico = RepositorioAnaliticoSQLite(caminho_banco_teste)
    repositorio_analitico.inicializar_banco()

    inserir_medicoes_centro(repositorio_central)

    imprimir_titulo("Buscando últimas medições centrais")
    medicoes = repositorio_central.listar_ultimas_medicoes_como_modelos(limite=6)
    for medicao in medicoes:
        print(
            f"{medicao.data_hora} | pulsos={medicao.pulsos} | "
            f"intervalo={medicao.chuva_intervalo_mm:.2f} mm | "
            f"acumulado={medicao.chuva_acumulada_mm:.2f} mm"
        )

    imprimir_titulo("Executando análise do evento")
    resultado = analisar_evento_chuva(medicoes)
    print(resultado.classificacao)

    imprimir_titulo("Persistindo resultado analítico")
    inserido = repositorio_analitico.inserir_ou_confirmar_analise(
        id_ultima_medicao_origem=3006,
        data_hora_ultima_medicao="2026-04-19 09:01:15",
        resultado=resultado,
    )
    print(f"Resultado persistido ou confirmado: {inserido}")

    imprimir_titulo("Contagem de análises")
    total = repositorio_analitico.contar_analises()
    print(f"Total de análises persistidas: {total}")

    imprimir_titulo("Listagem das análises")
    registros = repositorio_analitico.listar_todas(limite=20)
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

    imprimir_titulo("Regravando a mesma análise para validar idempotência")
    inserido_novamente = repositorio_analitico.inserir_ou_confirmar_analise(
        id_ultima_medicao_origem=3006,
        data_hora_ultima_medicao="2026-04-19 09:01:15",
        resultado=resultado,
    )
    print(f"Resultado persistido ou confirmado novamente: {inserido_novamente}")
    print(f"Total final de análises persistidas: {repositorio_analitico.contar_analises()}")


if __name__ == "__main__":
    main()