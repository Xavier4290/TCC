from app.modelos import Medicao
from pc.features_chuva import extrair_features_chuva


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def imprimir_features(features) -> None:
    """Mostra o conjunto de features calculadas."""
    for campo, valor in features.__dict__.items():
        print(f"{campo}: {valor}")


def main() -> None:
    """Valida o cálculo de features em cenários simulados."""
    cenario_progressivo = [
        Medicao("2026-04-19 06:00:00", 0, 0.00, 0.00),
        Medicao("2026-04-19 06:00:15", 1, 0.25, 0.25),
        Medicao("2026-04-19 06:00:30", 2, 0.50, 0.75),
        Medicao("2026-04-19 06:00:45", 4, 1.00, 1.75),
        Medicao("2026-04-19 06:01:00", 6, 1.50, 3.25),
        Medicao("2026-04-19 06:01:15", 8, 2.00, 5.25),
    ]

    cenario_intermitente = [
        Medicao("2026-04-19 06:10:00", 0, 0.00, 0.00),
        Medicao("2026-04-19 06:10:15", 2, 0.50, 0.50),
        Medicao("2026-04-19 06:10:30", 0, 0.00, 0.50),
        Medicao("2026-04-19 06:10:45", 1, 0.25, 0.75),
        Medicao("2026-04-19 06:11:00", 0, 0.00, 0.75),
        Medicao("2026-04-19 06:11:15", 3, 0.75, 1.50),
    ]

    imprimir_titulo("Features - cenário progressivo")
    features_progressivo = extrair_features_chuva(cenario_progressivo)
    imprimir_features(features_progressivo)

    imprimir_titulo("Features - cenário intermitente")
    features_intermitente = extrair_features_chuva(cenario_intermitente)
    imprimir_features(features_intermitente)


if __name__ == "__main__":
    main()