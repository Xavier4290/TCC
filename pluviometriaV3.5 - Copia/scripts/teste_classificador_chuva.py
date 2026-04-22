from app.modelos import Medicao
from pc.classificador_chuva import classificar_chuva
from pc.features_chuva import extrair_features_chuva


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def imprimir_resultado(nome_cenario: str, resultado) -> None:
    """Mostra o resultado da classificação."""
    print(f"Cenário: {nome_cenario}")
    for campo, valor in resultado.__dict__.items():
        print(f"{campo}: {valor}")


def main() -> None:
    """Valida o classificador de chuva em cenários simulados controlados."""
    cenario_sem_chuva = [
        Medicao("2026-04-19 07:00:00", 0, 0.00, 0.00),
        Medicao("2026-04-19 07:00:15", 0, 0.00, 0.00),
        Medicao("2026-04-19 07:00:30", 0, 0.00, 0.00),
        Medicao("2026-04-19 07:00:45", 0, 0.00, 0.00),
    ]

    cenario_intermitente = [
        Medicao("2026-04-19 07:10:00", 0, 0.00, 0.00),
        Medicao("2026-04-19 07:10:15", 2, 0.50, 0.50),
        Medicao("2026-04-19 07:10:30", 0, 0.00, 0.50),
        Medicao("2026-04-19 07:10:45", 1, 0.25, 0.75),
        Medicao("2026-04-19 07:11:00", 0, 0.00, 0.75),
        Medicao("2026-04-19 07:11:15", 3, 0.75, 1.50),
    ]

    cenario_progressivo = [
        Medicao("2026-04-19 07:20:00", 0, 0.00, 0.00),
        Medicao("2026-04-19 07:20:15", 1, 0.25, 0.25),
        Medicao("2026-04-19 07:20:30", 2, 0.50, 0.75),
        Medicao("2026-04-19 07:20:45", 4, 1.00, 1.75),
        Medicao("2026-04-19 07:21:00", 6, 1.50, 3.25),
        Medicao("2026-04-19 07:21:15", 8, 2.00, 5.25),
    ]

    cenario_persistente_forte = [
        Medicao("2026-04-19 07:30:00", 5, 1.25, 1.25),
        Medicao("2026-04-19 07:30:15", 6, 1.50, 2.75),
        Medicao("2026-04-19 07:30:30", 7, 1.75, 4.50),
        Medicao("2026-04-19 07:30:45", 8, 2.00, 6.50),
        Medicao("2026-04-19 07:31:00", 7, 1.75, 8.25),
        Medicao("2026-04-19 07:31:15", 6, 1.50, 9.75),
    ]

    cenarios = [
        ("sem_chuva", cenario_sem_chuva),
        ("intermitente", cenario_intermitente),
        ("progressivo", cenario_progressivo),
        ("persistente_forte", cenario_persistente_forte),
    ]

    for nome, medicoes in cenarios:
        imprimir_titulo(f"Classificação - {nome}")
        features = extrair_features_chuva(medicoes)
        resultado = classificar_chuva(features)
        imprimir_resultado(nome, resultado)


if __name__ == "__main__":
    main()