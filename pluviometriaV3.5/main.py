import time
from datetime import datetime

from app.cliente_envio import ClienteEnvioSocket
from app.coletor_gpio import ColetorGPIO
from app.coletor_simulado import ColetorSimulado
from app.config import (
    MANUTENCAO_LOCAL_HABILITADA,
    MODO_EXECUCAO,
    PADRAO_PULSOS_SIMULADOS,
)
from app.manutencao_local import ManutencaoLocal
from app.orquestrador import OrquestradorPluviometria
from app.repositorio_medicoes import RepositorioMedicoesSQLite
from app.sincronizador import SincronizadorMedicoes


def criar_coletor():
    """Cria o coletor conforme o modo de execução configurado."""
    if MODO_EXECUCAO == "simulado":
        return ColetorSimulado(
            instante_inicial=datetime.now().replace(microsecond=0),
            padrao_pulsos=PADRAO_PULSOS_SIMULADOS,
        )

    if MODO_EXECUCAO == "gpio":
        return ColetorGPIO()

    raise ValueError(
        f"MODO_EXECUCAO inválido: {MODO_EXECUCAO}. "
        "Use 'simulado' ou 'gpio'."
    )


def criar_manutencao_local(repositorio: RepositorioMedicoesSQLite):
    """Cria a manutenção local apenas quando ela estiver habilitada."""
    if not MANUTENCAO_LOCAL_HABILITADA:
        return None

    return ManutencaoLocal(repositorio=repositorio)


def main() -> None:
    """Inicia o sistema completo no modo configurado."""
    orquestrador = None

    try:
        repositorio = RepositorioMedicoesSQLite()
        coletor = criar_coletor()
        cliente_envio = ClienteEnvioSocket()
        sincronizador = SincronizadorMedicoes(repositorio, cliente_envio)
        manutencao_local = criar_manutencao_local(repositorio)

        orquestrador = OrquestradorPluviometria(
            repositorio=repositorio,
            coletor=coletor,
            sincronizador=sincronizador,
            manutencao_local=manutencao_local,
        )

        print(f"Modo de execução selecionado: {MODO_EXECUCAO}")
        print(f"Manutenção local habilitada: {MANUTENCAO_LOCAL_HABILITADA}")
        orquestrador.iniciar()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nEncerramento solicitado pelo usuário.")
    except Exception as erro:
        print(f"Erro ao iniciar o sistema: {erro}")
    finally:
        if orquestrador is not None:
            orquestrador.parar()


if __name__ == "__main__":
    main()