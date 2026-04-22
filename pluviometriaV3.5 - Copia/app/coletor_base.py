from abc import ABC, abstractmethod

from .modelos import Medicao


class ColetorBase(ABC):
    """Define o contrato mínimo de um coletor de medições."""

    @abstractmethod
    def coletar_medicao(self) -> Medicao:
        """
        Retorna a próxima medição consolidada.
        Cada implementação decide como obter os dados.
        """
        raise NotImplementedError