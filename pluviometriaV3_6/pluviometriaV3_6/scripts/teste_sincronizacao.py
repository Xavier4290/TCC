from datetime import datetime
from pathlib import Path

from app.cliente_envio import ClienteEnvioSocket
from app.coletor_simulado import ColetorSimulado
from app.config import DATA_DIR
from app.repositorio_medicoes import RepositorioMedicoesSQLite
from app.sincronizador import SincronizadorMedicoes


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída do teste."""
    print("\n" + "=" * 70)
    print(texto)
    print("=" * 70)


def imprimir_medicoes(medicoes) -> None:
    """Mostra as medições retornadas pelo repositório"""
    for medicao in medicoes:
        print(
            f"ID={medicao.id} | data_hora={medicao.data_hora} | "
            f"pulsos={medicao.pulsos} | intervalo={medicao.chuva_intervalo_mm:.2f} mm | "
            f"acumulado={medicao.chuva_acumulada_mm:.2f} mm | "
            f"status={medicao.status_sync} | tentativas={medicao.tentativas_envio} | "
            f"erro={medicao.ultimo_erro}"
        )


def preparar_banco_teste(caminho_banco: Path) -> None:
    """Remove o banco de teste anterior para garantir execução limpa"""
    caminho_banco.parent.mkdir(parents=True, exist_ok=True)

    if caminho_banco.exists():
        caminho_banco.unlink()


def main() -> None:
    """Gera pendências simuladas e executa uma tentativa única de sincronização"""
    caminho_banco_teste = DATA_DIR / "teste_sincronizacao.db"
    preparar_banco_teste(caminho_banco_teste)

    repositorio = RepositorioMedicoesSQLite(caminho_banco_teste)
    repositorio.inicializar_banco()

    coletor = ColetorSimulado(
        instante_inicial=datetime(2026, 4, 12, 11, 0, 0)
    )

    pulsos_simulados = [1, 0, 3, 4, 2, 0]

    imprimir_titulo("Inserindo medições pendentes no banco de teste")

    for pulsos in pulsos_simulados:
        medicao = coletor.gerar_medicao(pulsos)
        repositorio.inserir_medicao(medicao)

    pendentes_antes = repositorio.buscar_pendentes(limite=10)
    imprimir_medicoes(pendentes_antes)

    cliente_envio = ClienteEnvioSocket()
    sincronizador = SincronizadorMedicoes(repositorio, cliente_envio)

    imprimir_titulo("Executando sincronização")
    resultado = sincronizador.sincronizar_uma_vez()
    print(resultado)

    imprimir_titulo("Estado final das medições")
    medicoes_finais = repositorio.listar_todas()
    imprimir_medicoes(medicoes_finais)


if __name__ == "__main__":
    main()