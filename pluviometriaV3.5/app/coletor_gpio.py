from .coletor_base import ColetorBase
from .config import GPIO_BOUNCETIME_MS, GPIO_PIN, INTERVALO_MEDICAO_SEGUNDOS, MM_POR_PULSO
from .modelos import Medicao


class ColetorGPIO(ColetorBase):
    """
    Esqueleto do coletor real para Raspberry Pi.
    Nesta etapa, o objetivo é preparar a estrutura e validar o ambiente.
    """

    def __init__(self) -> None:
        self.gpio_pin = GPIO_PIN
        self.bouncetime_ms = GPIO_BOUNCETIME_MS
        self.intervalo_medicao_segundos = INTERVALO_MEDICAO_SEGUNDOS
        self.mm_por_pulso = MM_POR_PULSO
        self._gpio_modulo = self._importar_gpio()

    def coletar_medicao(self) -> Medicao:
        """
        Futuramente fará a leitura dos pulsos reais no intervalo configurado
        e retornará uma medição consolidada.
        """
        raise NotImplementedError(
            "O modo GPIO foi habilitado, mas a leitura real do sensor ainda "
            "não foi implementada nesta etapa do projeto."
        )

    def _importar_gpio(self):
        """
        Tenta importar a biblioteca do Raspberry.
        Falha com mensagem clara quando o código está rodando fora do ambiente real.
        """
        try:
            import RPi.GPIO as GPIO  # type: ignore
            return GPIO
        except ModuleNotFoundError as erro:
            raise RuntimeError(
                "A biblioteca RPi.GPIO não está disponível neste ambiente. "
                "Use MODO_EXECUCAO = 'simulado' no PC ou execute no Raspberry Pi "
                "com o ambiente apropriado."
            ) from erro