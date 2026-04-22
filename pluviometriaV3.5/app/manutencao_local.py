from datetime import datetime, timedelta
from typing import Dict

from .config import RETENCAO_LOCAL_ENVIADOS_HORAS
from .repositorio_medicoes import RepositorioMedicoesSQLite


class ManutencaoLocal:
    """
    Executa rotinas de manutenção do banco local de medições.
    Nesta fase, a manutenção atua apenas sobre registros ENVIADO antigos.
    """

    def __init__(
        self,
        repositorio: RepositorioMedicoesSQLite,
        retencao_enviados_horas: float = RETENCAO_LOCAL_ENVIADOS_HORAS,
    ) -> None:
        self.repositorio = repositorio
        self.retencao_enviados_horas = retencao_enviados_horas
        self._validar_configuracao()

    def executar_limpeza_enviados_antigos(self) -> Dict[str, object]:
        """
        Remove registros ENVIADO cujo enviado_em seja mais antigo que a política de retenção.
        Retorna um resumo da execução para facilitar testes e logs.
        """
        data_limite = self._calcular_data_limite()
        removidos = self.repositorio.remover_medicoes_enviadas_mais_antigas_que(data_limite)

        return {
            "retencao_horas": self.retencao_enviados_horas,
            "data_limite": data_limite,
            "removidos": removidos,
        }

    def _calcular_data_limite(self) -> str:
        """Calcula a data limite da retenção no formato usado pelo banco."""
        agora = datetime.now()
        limite = agora - timedelta(hours=self.retencao_enviados_horas)
        return limite.strftime("%Y-%m-%d %H:%M:%S")

    def _validar_configuracao(self) -> None:
        """Valida os parâmetros básicos da manutenção local."""
        if self.retencao_enviados_horas <= 0:
            raise ValueError("A retenção de enviados em horas deve ser maior que zero.")