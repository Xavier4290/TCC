import time
from datetime import datetime

from app.cliente_envio import ClienteEnvioSocket
from app.coletor_simulado import ColetorSimulado
from app.config import PADRAO_PULSOS_SIMULADOS
from app.orquestrador import OrquestradorPluviometriaSimulada
from app.repositorio_medicoes import RepositorioMedicoesSQLite
from app.sincronizador import SincronizadorMedicoes


def main() -> None:
    """Inicia o sistema completo em modo simulado."""
    repositorio = RepositorioMedicoesSQLite()
    coletor = ColetorSimulado(
        instante_inicial=datetime.now().replace(microsecond=0)
    )
    cliente_envio = ClienteEnvioSocket()
    sincronizador = SincronizadorMedicoes(repositorio, cliente_envio)

    orquestrador = OrquestradorPluviometriaSimulada(
        repositorio=repositorio,
        coletor=coletor,
        sincronizador=sincronizador,
        padrao_pulsos=PADRAO_PULSOS_SIMULADOS,
    )

    orquestrador.iniciar()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerramento solicitado pelo usuário.")
    finally:
        orquestrador.parar()


if __name__ == "__main__":
    main()