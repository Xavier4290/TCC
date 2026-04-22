from app.coletor_gpio import ColetorGPIO
from app.coletor_simulado import ColetorSimulado
from app.config import MODO_EXECUCAO, PADRAO_PULSOS_SIMULADOS
from datetime import datetime


def main() -> None:
    """Valida a criação do coletor conforme o modo configurado."""
    print(f"Modo configurado: {MODO_EXECUCAO}")

    if MODO_EXECUCAO == "simulado":
        coletor = ColetorSimulado(
            instante_inicial=datetime.now().replace(microsecond=0),
            padrao_pulsos=PADRAO_PULSOS_SIMULADOS,
        )
        medicao = coletor.coletar_medicao()
        print("Coletor simulado criado com sucesso.")
        print(
            f"Primeira medição simulada: data_hora={medicao.data_hora} | "
            f"pulsos={medicao.pulsos} | "
            f"intervalo={medicao.chuva_intervalo_mm:.2f} mm | "
            f"acumulado={medicao.chuva_acumulada_mm:.2f} mm"
        )
        return

    if MODO_EXECUCAO == "gpio":
        coletor = ColetorGPIO()
        print(f"Coletor GPIO criado com sucesso: {coletor}")
        return

    raise ValueError(f"MODO_EXECUCAO inválido: {MODO_EXECUCAO}")


if __name__ == "__main__":
    main()