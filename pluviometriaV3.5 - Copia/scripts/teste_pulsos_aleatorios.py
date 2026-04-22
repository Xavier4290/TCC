from datetime import datetime

from app.coletor_simulado import ColetorSimulado


def main() -> None:
    """Gera medições simuladas em modo aleatório para validar a faixa e a variabilidade."""
    coletor = ColetorSimulado(
        instante_inicial=datetime(2026, 4, 19, 2, 0, 0),
        usar_pulsos_aleatorios=True,
    )

    print("Gerando 10 medições aleatórias controladas:\n")

    for _ in range(10):
        medicao = coletor.coletar_medicao()
        print(
            f"{medicao.data_hora} | pulsos={medicao.pulsos} | "
            f"intervalo={medicao.chuva_intervalo_mm:.2f} mm | "
            f"acumulado={medicao.chuva_acumulada_mm:.2f} mm"
        )


if __name__ == "__main__":
    main()