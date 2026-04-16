from datetime import datetime
from pathlib import Path

from app.config import DATA_DIR
from app.coletor_simulado import ColetorSimulado
from app.repositorio_medicoes import RepositorioMedicoesSQLite


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída do teste."""
    print("\n" + "=" * 70)
    print(texto)
    print("=" * 70)


def imprimir_medicoes(medicoes) -> None:
    """Mostra as medições retornadas pelo repositório."""
    for medicao in medicoes:
        print(
            f"ID={medicao.id} | data_hora={medicao.data_hora} | "
            f"pulsos={medicao.pulsos} | intervalo={medicao.chuva_intervalo_mm:.2f} mm | "
            f"acumulado={medicao.chuva_acumulada_mm:.2f} mm | "
            f"status={medicao.status_sync}"
        )


def preparar_banco_teste(caminho_banco: Path) -> None:
    """Remove o banco de teste anterior para garantir execução limpa."""
    caminho_banco.parent.mkdir(parents=True, exist_ok=True)

    if caminho_banco.exists():
        caminho_banco.unlink()


def main() -> None:
    """Executa um fluxo de teste da coleta simulada integrada ao repositório."""
    caminho_banco_teste = DATA_DIR / "teste_coleta_simulada.db"
    preparar_banco_teste(caminho_banco_teste)

    repositorio = RepositorioMedicoesSQLite(caminho_banco_teste)
    repositorio.inicializar_banco()

    coletor = ColetorSimulado(
        instante_inicial=datetime(2026, 4, 12, 10, 0, 0)
    )

    # Cenário simples de teste:
    # sem chuva, chuva fraca, chuva moderada, pico curto, sem chuva, chuva leve.
    pulsos_simulados = [0, 2, 4, 12, 0, 1]

    imprimir_titulo("Gerando medições simuladas e persistindo no SQLite")

    ids_criados = []

    for pulsos in pulsos_simulados:
        medicao = coletor.gerar_medicao(pulsos)
        id_criado = repositorio.inserir_medicao(medicao)
        ids_criados.append(id_criado)

        print(
            f"ID={id_criado} | data_hora={medicao.data_hora} | "
            f"pulsos={medicao.pulsos} | intervalo={medicao.chuva_intervalo_mm:.2f} mm | "
            f"acumulado={medicao.chuva_acumulada_mm:.2f} mm"
        )

    print(f"\nIDs criados: {ids_criados}")
    print(f"Total de medições no banco de teste: {repositorio.contar_medicoes()}")

    imprimir_titulo("Listando todas as medições persistidas")
    medicoes = repositorio.listar_todas()
    imprimir_medicoes(medicoes)

    imprimir_titulo("Buscando pendentes")
    pendentes = repositorio.buscar_pendentes(limite=10)
    imprimir_medicoes(pendentes)


if __name__ == "__main__":
    main()