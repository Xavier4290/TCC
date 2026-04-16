from datetime import datetime, timedelta
from typing import Iterable, List

from .config import INTERVALO_MEDICAO_SEGUNDOS, MM_POR_PULSO
from .modelos import Medicao


class ColetorSimulado:
    """Gera medições artificiais para validar a lógica sem depender de hardware real."""

    def __init__(
        self,
        instante_inicial: datetime,
        mm_por_pulso: float = MM_POR_PULSO,
        intervalo_medicao_segundos: int = INTERVALO_MEDICAO_SEGUNDOS,
        chuva_acumulada_inicial_mm: float = 0.0,
    ) -> None:
        self.instante_atual = instante_inicial
        self.mm_por_pulso = mm_por_pulso
        self.intervalo_medicao_segundos = intervalo_medicao_segundos
        self.chuva_acumulada_mm = chuva_acumulada_inicial_mm

        self._validar_estado_inicial()

    def gerar_medicao(self, pulsos: int) -> Medicao:
        """
        Gera uma medição simulada para o instante atual e avança o relógio interno.
        Cada chamada representa um novo intervalo de coleta.
        """
        self._validar_pulsos(pulsos)

        chuva_intervalo_mm = pulsos * self.mm_por_pulso
        self.chuva_acumulada_mm += chuva_intervalo_mm

        medicao = Medicao(
            data_hora=self.instante_atual.strftime("%Y-%m-%d %H:%M:%S"),
            pulsos=pulsos,
            chuva_intervalo_mm=round(chuva_intervalo_mm, 2),
            chuva_acumulada_mm=round(self.chuva_acumulada_mm, 2),
        )

        self.instante_atual += timedelta(seconds=self.intervalo_medicao_segundos)
        return medicao

    def gerar_medicoes_sequenciais(self, pulsos_por_intervalo: Iterable[int]) -> List[Medicao]:
        """Gera várias medições em sequência a partir de uma lista de pulsos."""
        medicoes = []

        for pulsos in pulsos_por_intervalo:
            medicoes.append(self.gerar_medicao(pulsos))

        return medicoes

    def _validar_estado_inicial(self) -> None:
        """Valida os parâmetros recebidos na criação do simulador."""
        if self.mm_por_pulso <= 0:
            raise ValueError("MM_POR_PULSO deve ser maior que zero.")

        if self.intervalo_medicao_segundos <= 0:
            raise ValueError("O intervalo de medição deve ser maior que zero.")

        if self.chuva_acumulada_mm < 0:
            raise ValueError("A chuva acumulada inicial não pode ser negativa.")

    def _validar_pulsos(self, pulsos: int) -> None:
        """Impede geração de medições com quantidade inválida de pulsos."""
        if not isinstance(pulsos, int):
            raise TypeError("A quantidade de pulsos deve ser um número inteiro.")

        if pulsos < 0:
            raise ValueError("A quantidade de pulsos não pode ser negativa.")