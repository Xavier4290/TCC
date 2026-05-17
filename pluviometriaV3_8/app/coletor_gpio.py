import time
import threading
from datetime import datetime
from .coletor_base import ColetorBase
from .config import GPIO_BOUNCETIME_MS, GPIO_PIN, INTERVALO_MEDICAO_SEGUNDOS, MM_POR_PULSO
from .modelos import Medicao


class ColetorGPIO(ColetorBase):
    """
    Coletor real para Raspberry Pi usando interrupção GPIO.
    Conta pulsos em background durante o intervalo de medição.
    """

    def __init__(self) -> None:
        self.gpio_pin = GPIO_PIN
        self.bouncetime_ms = GPIO_BOUNCETIME_MS
        self.intervalo = INTERVALO_MEDICAO_SEGUNDOS
        self.mm_por_pulso = MM_POR_PULSO
        self._pulsos = 0
        self._lock = threading.Lock()
        self._gpio = self._importar_gpio()
        self._setup_gpio()
        self.chuva_acumulada_mm = 0.0

    def _importar_gpio(self):
        try:
            import RPi.GPIO as GPIO
            return GPIO
        except ModuleNotFoundError:
            raise RuntimeError(
                "Biblioteca RPi.GPIO não encontrada. Execute no Raspberry Pi ou use MODO_EXECUCAO='simulado' no PC."
            )

    def _setup_gpio(self):
        self._gpio.setmode(self._gpio.BCM)
        self._gpio.setup(self.gpio_pin, self._gpio.IN, pull_up_down=self._gpio.PUD_UP)
        self._gpio.add_event_detect(
            self.gpio_pin,
            self._gpio.FALLING,
            callback=self._callback_pulso,
            bouncetime=self.bouncetime_ms
        )

    def _callback_pulso(self, channel):
        with self._lock:
            self._pulsos += 1

    def coletar_medicao(self) -> Medicao:
        """Aguarda o intervalo, conta os pulsos e retorna a medição."""
        # Dorme o intervalo completo
        time.sleep(self.intervalo)
        # Captura os pulsos e reseta o contador
        with self._lock:
            pulsos = self._pulsos
            self._pulsos = 0

        chuva_intervalo = pulsos * self.mm_por_pulso
        self.chuva_acumulada_mm += chuva_intervalo

        data_hora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return Medicao(
            data_hora=data_hora_str,
            pulsos=pulsos,
            chuva_intervalo_mm=round(chuva_intervalo, 2),
            chuva_acumulada_mm=round(self.chuva_acumulada_mm, 2),
        )

    def __del__(self):
        if hasattr(self, '_gpio'):
            self._gpio.cleanup()