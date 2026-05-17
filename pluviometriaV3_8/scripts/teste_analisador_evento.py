from app.modelos import Medicao
from pc.analisador_evento import analisar_evento_chuva


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def imprimir_resultado(nome_cenario: str, resultado) -> None:
    """Mostra o resultado consolidado do analisador."""
    print(f"Cenário: {nome_cenario}")

    print("\n[Features]")
    for campo, valor in resultado.features.__dict__.items():
        print(f"{campo}: {valor}")

    print("\n[Classificação]")
    for campo, valor in resultado.classificacao.__dict__.items():
        print(f"{campo}: {valor}")


def main() -> None:
    """Valida o analisador de evento em cenários simulados."""
    cenario_intermitente = [
        Medicao("2026-04-19 08:00:00", 0, 0.00, 0.00),
        Medicao("2026-04-19 08:00:15", 2, 0.50, 0.50),
        Medicao("2026-04-19 08:00:30", 0, 0.00, 0.50),
        Medicao("2026-04-19 08:00:45", 1, 0.25, 0.75),
        Medicao("2026-04-19 08:01:00", 0, 0.00, 0.75),
        Medicao("2026-04-19 08:01:15", 3, 0.75, 1.50),
    ]

    cenario_progressivo = [
        Medicao("2026-04-19 08:10:00", 0, 0.00, 0.00),
        Medicao("2026-04-19 08:10:15", 1, 0.25, 0.25),
        Medicao("2026-04-19 08:10:30", 2, 0.50, 0.75),
        Medicao("2026-04-19 08:10:45", 4, 1.00, 1.75),
        Medicao("2026-04-19 08:11:00", 6, 1.50, 3.25),
        Medicao("2026-04-19 08:11:15", 8, 2.00, 5.25),
    ]

    cenarios = [
        ("intermitente", cenario_intermitente),
        ("progressivo", cenario_progressivo),
    ]

    for nome, medicoes in cenarios:
        imprimir_titulo(f"Analisador de evento - {nome}")
        resultado = analisar_evento_chuva(medicoes)
        imprimir_resultado(nome, resultado)


if __name__ == "__main__":
    main()