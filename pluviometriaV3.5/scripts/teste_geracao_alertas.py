from pathlib import Path

from app.config import DATA_DIR
from app.modelos import Medicao
from pc.analisador_evento import analisar_evento_chuva
from pc.gerador_alertas import gerar_alerta
from pc.repositorio_alertas import RepositorioAlertasSQLite


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
    """Valida a geração e persistência de alertas a partir da análise."""
    caminho_banco_teste = DATA_DIR / "teste_alertas_pc.db"
    preparar_banco_teste(caminho_banco_teste)

    repositorio_alertas = RepositorioAlertasSQLite(caminho_banco_teste)
    repositorio_alertas.inicializar_banco()

    cenario_intermitente = [
        Medicao("2026-04-20 02:00:00", 0, 0.00, 0.00),
        Medicao("2026-04-20 02:00:15", 2, 0.50, 0.50),
        Medicao("2026-04-20 02:00:30", 0, 0.00, 0.50),
        Medicao("2026-04-20 02:00:45", 1, 0.25, 0.75),
        Medicao("2026-04-20 02:01:00", 0, 0.00, 0.75),
        Medicao("2026-04-20 02:01:15", 3, 0.75, 1.50),
    ]

    cenario_progressivo = [
        Medicao("2026-04-20 02:10:00", 0, 0.00, 0.00),
        Medicao("2026-04-20 02:10:15", 1, 0.25, 0.25),
        Medicao("2026-04-20 02:10:30", 2, 0.50, 0.75),
        Medicao("2026-04-20 02:10:45", 4, 1.00, 1.75),
        Medicao("2026-04-20 02:11:00", 6, 1.50, 3.25),
        Medicao("2026-04-20 02:11:15", 8, 2.00, 5.25),
    ]

    cenarios = [
        ("intermitente", 5001, "2026-04-20 02:01:15", cenario_intermitente),
        ("progressivo", 5002, "2026-04-20 02:11:15", cenario_progressivo),
    ]

    for nome, id_ultima, data_hora_ultima, medicoes in cenarios:
        imprimir_titulo(f"Geração de alerta - {nome}")

        resultado_analise = analisar_evento_chuva(medicoes)
        resultado_alerta = gerar_alerta(resultado_analise)

        print("[Analise]")
        print(resultado_analise.classificacao)

        print("\n[Alerta]")
        print(resultado_alerta)

        if resultado_alerta.deve_persistir:
            persistido = repositorio_alertas.inserir_ou_confirmar_alerta(
                id_ultima_medicao_origem=id_ultima,
                data_hora_ultima_medicao=data_hora_ultima,
                resultado_alerta=resultado_alerta,
            )
            print(f"\nPersistido ou confirmado: {persistido}")
        else:
            print("\nAlerta não persistido por regra de negócio.")

    imprimir_titulo("Resumo final dos alertas persistidos")
    print(f"Total de alertas: {repositorio_alertas.contar_alertas()}")

    for alerta in repositorio_alertas.listar_todos(limite=20):
        print(
            f"id={alerta['id']} | "
            f"id_ultima_medicao_origem={alerta['id_ultima_medicao_origem']} | "
            f"nivel_alerta={alerta['nivel_alerta']} | "
            f"mensagem={alerta['mensagem_alerta']} | "
            f"gerado_em={alerta['gerado_em']}"
        )


if __name__ == "__main__":
    main()