from datetime import datetime, timedelta
from typing import Iterable, List, Optional
import itertools
import random

from .coletor_base import ColetorBase
from .config import (
    INTERVALO_MEDICAO_SEGUNDOS,
    MM_POR_PULSO,
    PADRAO_PULSOS_SIMULADOS,
    PESOS_PULSOS_SIMULADOS,
    PULSO_MAXIMO_SIMULADO,
    PULSO_MINIMO_SIMULADO,
    USAR_PULSOS_ALEATORIOS,
)
from .modelos import Medicao


class ColetorSimulado(ColetorBase):
    """Gera medições artificiais para validar a lógica sem depender de hardware real."""

    def __init__(
        self,
        instante_inicial: datetime,
        mm_por_pulso: float = MM_POR_PULSO,
        intervalo_medicao_segundos: int = INTERVALO_MEDICAO_SEGUNDOS,
        chuva_acumulada_inicial_mm: float = 0.0,
        padrao_pulsos: Optional[Iterable[int]] = None,
        usar_pulsos_aleatorios: bool = USAR_PULSOS_ALEATORIOS,
        pulso_minimo: int = PULSO_MINIMO_SIMULADO,
        pulso_maximo: int = PULSO_MAXIMO_SIMULADO,
        pesos_pulsos: Iterable[int] = PESOS_PULSOS_SIMULADOS,
    ) -> None:
        self.instante_atual = instante_inicial
        self.mm_por_pulso = mm_por_pulso
        self.intervalo_medicao_segundos = intervalo_medicao_segundos
        self.chuva_acumulada_mm = chuva_acumulada_inicial_mm

        self.padrao_pulsos = tuple(padrao_pulsos or PADRAO_PULSOS_SIMULADOS)
        self.usar_pulsos_aleatorios = usar_pulsos_aleatorios
        self.pulso_minimo = pulso_minimo
        self.pulso_maximo = pulso_maximo
        self.pesos_pulsos = tuple(pesos_pulsos)

        self._ciclo_pulsos = itertools.cycle(self.padrao_pulsos)

        self._validar_estado_inicial()

    def coletar_medicao(self) -> Medicao:
        """
        Gera automaticamente a próxima medição.
        Pode usar padrão fixo ou pulsos aleatórios controlados.
        """
        pulsos = self._obter_proximo_pulso()
        return self.gerar_medicao(pulsos)

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

    def _obter_proximo_pulso(self) -> int:
        """Decide se usa padrão fixo ou sorteio aleatório controlado."""
        if not self.usar_pulsos_aleatorios:
            return next(self._ciclo_pulsos)

        valores_possiveis = list(range(self.pulso_minimo, self.pulso_maximo + 1))
        pulsos = random.choices(
            population=valores_possiveis,
            weights=self.pesos_pulsos,
            k=1,
        )[0]

        return int(pulsos)

    def _validar_estado_inicial(self) -> None:
        """Valida os parâmetros recebidos na criação do simulador."""
        if self.mm_por_pulso <= 0:
            raise ValueError("MM_POR_PULSO deve ser maior que zero.")

        if self.intervalo_medicao_segundos <= 0:
            raise ValueError("O intervalo de medição deve ser maior que zero.")

        if self.chuva_acumulada_mm < 0:
            raise ValueError("A chuva acumulada inicial não pode ser negativa.")

        if not self.padrao_pulsos:
            raise ValueError("O padrão de pulsos simulados não pode ser vazio.")

        if self.pulso_minimo < 0 or self.pulso_maximo < 0:
            raise ValueError("Os limites de pulsos simulados não podem ser negativos.")

        if self.pulso_minimo > self.pulso_maximo:
            raise ValueError("O pulso mínimo não pode ser maior que o pulso máximo.")

        quantidade_valores = self.pulso_maximo - self.pulso_minimo + 1

        if len(self.pesos_pulsos) != quantidade_valores:
            raise ValueError(
                "A quantidade de pesos deve corresponder à quantidade de valores "
                "possíveis entre pulso mínimo e pulso máximo."
            )

        if any(peso < 0 for peso in self.pesos_pulsos):
            raise ValueError("Os pesos dos pulsos simulados não podem ser negativos.")

        if sum(self.pesos_pulsos) == 0:
            raise ValueError("A soma dos pesos dos pulsos simulados não pode ser zero.")

    def _validar_pulsos(self, pulsos: int) -> None:
        """Impede geração de medições com quantidade inválida de pulsos."""
        if not isinstance(pulsos, int):
            raise TypeError("A quantidade de pulsos deve ser um número inteiro.")

        if pulsos < 0:
            raise ValueError("A quantidade de pulsos não pode ser negativa.")