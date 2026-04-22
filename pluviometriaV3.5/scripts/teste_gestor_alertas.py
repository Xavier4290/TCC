from pathlib import Path

from app.config import DATA_DIR
from app.modelos import Medicao
from pc.analisador_evento import analisar_evento_chuva
from pc.gerador_alertas import gerar_alerta
from pc.gestor_alertas import GestorAlertas
from pc.repositorio_alertas_ciclo import RepositorioAlertasCicloSQLite


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


def main() -> None:
    """Valida abertura, atualização e encerramento do ciclo de vida do alerta."""
    caminho_banco_teste = DATA_DIR / "teste_gestor_alertas.db"
    preparar_banco_teste(caminho_banco_teste)

    repositorio = RepositorioAlertasCicloSQLite(caminho_banco_teste)
    repositorio.inicializar_banco()

    gestor = GestorAlertas(repositorio)

    cenario_critico_1 = [
        Medicao("2026-04-20 04:00:00", 0, 0.00, 0.00),
        Medicao("2026-04-20 04:00:15", 1, 0.25, 0.25),
        Medicao("2026-04-20 04:00:30", 2, 0.50, 0.75),
        Medicao("2026-04-20 04:00:45", 4, 1.00, 1.75),
        Medicao("2026-04-20 04:01:00", 6, 1.50, 3.25),
        Medicao("2026-04-20 04:01:15", 8, 2.00, 5.25),
    ]

    cenario_critico_2 = [
        Medicao("2026-04-20 04:01:30", 5, 1.25, 6.50),
        Medicao("2026-04-20 04:01:45", 7, 1.75, 8.25),
        Medicao("2026-04-20 04:02:00", 8, 2.00, 10.25),
        Medicao("2026-04-20 04:02:15", 6, 1.50, 11.75),
        Medicao("2026-04-20 04:02:30", 4, 1.00, 12.75),
        Medicao("2026-04-20 04:02:45", 3, 0.75, 13.50),
    ]

    cenario_normalizado = [
        Medicao("2026-04-20 04:03:00", 0, 0.00, 13.50),
        Medicao("2026-04-20 04:03:15", 0, 0.00, 13.50),
        Medicao("2026-04-20 04:03:30", 1, 0.25, 13.75),
        Medicao("2026-04-20 04:03:45", 0, 0.00, 13.75),
        Medicao("2026-04-20 04:04:00", 0, 0.00, 13.75),
        Medicao("2026-04-20 04:04:15", 0, 0.00, 13.75),
    ]

    cenarios = [
        ("abertura", 7001, "2026-04-20 04:01:15", cenario_critico_1),
        ("atualizacao", 7002, "2026-04-20 04:02:45", cenario_critico_2),
        ("encerramento", 7003, "2026-04-20 04:04:15", cenario_normalizado),
    ]

    for nome, id_ultima, data_hora_ultima, medicoes in cenarios:
        imprimir_titulo(f"Gestão de alerta - {nome}")

        resultado_analise = analisar_evento_chuva(medicoes)
        resultado_alerta = gerar_alerta(resultado_analise)
        resultado_gestao = gestor.processar_resultado_alerta(
            id_ultima_medicao_origem=id_ultima,
            data_hora_ultima_medicao=data_hora_ultima,
            resultado_alerta=resultado_alerta,
        )

        print("[Análise]")
        print(resultado_analise.classificacao)

        print("\n[Alerta gerado]")
        print(resultado_alerta)

        print("\n[Gestão]")
        print(resultado_gestao)

    imprimir_titulo("Resumo final do ciclo de alertas")
    print(f"Total de alertas registrados: {repositorio.contar_alertas()}")

    for alerta in repositorio.listar_todos(limite=20):
        print(
            f"id={alerta['id']} | "
            f"status={alerta['status_alerta']} | "
            f"nivel_atual={alerta['nivel_alerta_atual']} | "
            f"nivel_maximo={alerta['nivel_alerta_maximo']} | "
            f"primeira_medicao_origem={alerta['primeira_medicao_origem']} | "
            f"ultima_medicao_origem={alerta['ultima_medicao_origem']} | "
            f"quantidade_atualizacoes={alerta['quantidade_atualizacoes']} | "
            f"encerrado_em={alerta['encerrado_em']}"
        )


if __name__ == "__main__":
    main()