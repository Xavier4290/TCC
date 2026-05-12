from app.modelos import Medicao
from pc.segmentador_janela_analitica import segmentar_janela_analitica


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def imprimir_segmento(resultado) -> None:
    """Mostra o resultado da segmentação."""
    print(f"segmento_valido: {resultado.segmento_valido}")
    print(f"motivo: {resultado.motivo}")
    print("medicoes_segmentadas:")

    for medicao in resultado.medicoes_segmentadas:
        print(
            f"  {medicao.data_hora} | pulsos={medicao.pulsos} | "
            f"intervalo={medicao.chuva_intervalo_mm:.2f} | "
            f"acumulado={medicao.chuva_acumulada_mm:.2f}"
        )


def main() -> None:
    """Valida a segmentação de janelas contínuas e coerentes."""
    cenario_continuo = [
        Medicao("2026-04-20 01:00:00", 1, 0.25, 0.25),
        Medicao("2026-04-20 01:00:15", 2, 0.50, 0.75),
        Medicao("2026-04-20 01:00:30", 4, 1.00, 1.75),
        Medicao("2026-04-20 01:00:45", 6, 1.50, 3.25),
    ]

    cenario_com_salto = [
        Medicao("2026-04-20 01:10:00", 1, 0.25, 0.25),
        Medicao("2026-04-20 01:10:15", 2, 0.50, 0.75),
        Medicao("2026-04-20 01:14:00", 4, 1.00, 1.75),
        Medicao("2026-04-20 01:14:15", 6, 1.50, 3.25),
    ]

    cenario_com_reinicio_acumulado = [
        Medicao("2026-04-20 01:20:00", 5, 1.25, 10.00),
        Medicao("2026-04-20 01:20:15", 4, 1.00, 11.00),
        Medicao("2026-04-20 01:20:30", 2, 0.50, 0.50),
        Medicao("2026-04-20 01:20:45", 3, 0.75, 1.25),
    ]

    cenarios = [
        ("continuo", cenario_continuo),
        ("com_salto", cenario_com_salto),
        ("com_reinicio_acumulado", cenario_com_reinicio_acumulado),
    ]

    for nome, medicoes in cenarios:
        imprimir_titulo(f"Segmentação - {nome}")
        resultado = segmentar_janela_analitica(medicoes)
        imprimir_segmento(resultado)


if __name__ == "__main__":
    main()