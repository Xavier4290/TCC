import itertools
import threading
from datetime import datetime
from typing import Iterable, Optional

from .config import (
    INTERVALO_MEDICAO_SEGUNDOS,
    INTERVALO_VERIFICACAO_PENDENCIAS_SEGUNDOS,
    LIMITE_LOTE_SINCRONIZACAO,
    TEMPO_MAXIMO_ESPERA_ENVIO_SEGUNDOS,
)
from .coletor_simulado import ColetorSimulado
from .repositorio_medicoes import RepositorioMedicoesSQLite
from .sincronizador import SincronizadorMedicoes


class OrquestradorPluviometriaSimulada:
    """Executa continuamente a coleta simulada e a sincronização em threads separadas."""

    def __init__(
        self,
        repositorio: RepositorioMedicoesSQLite,
        coletor: ColetorSimulado,
        sincronizador: SincronizadorMedicoes,
        padrao_pulsos: Iterable[int],
        intervalo_medicao_segundos: int = INTERVALO_MEDICAO_SEGUNDOS,
        intervalo_verificacao_pendencias_segundos: int = INTERVALO_VERIFICACAO_PENDENCIAS_SEGUNDOS,
        limite_lote: int = LIMITE_LOTE_SINCRONIZACAO,
        tempo_maximo_espera_envio_segundos: int = TEMPO_MAXIMO_ESPERA_ENVIO_SEGUNDOS,
    ) -> None:
        self.repositorio = repositorio
        self.coletor = coletor
        self.sincronizador = sincronizador
        self.intervalo_medicao_segundos = intervalo_medicao_segundos
        self.intervalo_verificacao_pendencias_segundos = intervalo_verificacao_pendencias_segundos
        self.limite_lote = limite_lote
        self.tempo_maximo_espera_envio_segundos = tempo_maximo_espera_envio_segundos

        self._evento_parada = threading.Event()
        self._thread_coleta: Optional[threading.Thread] = None
        self._thread_sincronizacao: Optional[threading.Thread] = None
        self._padrao_pulsos = tuple(padrao_pulsos)
        self._ciclo_pulsos = itertools.cycle(self._padrao_pulsos)

        self._validar_configuracao()

    def iniciar(self) -> None:
        """Inicializa o banco e inicia as duas rotinas contínuas."""
        self.repositorio.inicializar_banco()

        self._thread_coleta = threading.Thread(
            target=self._loop_coleta,
            name="thread_coleta_simulada",
            daemon=True,
        )
        self._thread_sincronizacao = threading.Thread(
            target=self._loop_sincronizacao,
            name="thread_sincronizacao",
            daemon=True,
        )

        print("Iniciando coleta contínua em modo simulado.")
        print("A primeira medição será consolidada após o primeiro intervalo completo.")
        print(
            f"Intervalo de medição: {self.intervalo_medicao_segundos}s | "
            f"Verificação de pendências: {self.intervalo_verificacao_pendencias_segundos}s | "
            f"Lote: até {self.limite_lote} registro(s) | "
            f"Tempo máximo de espera para envio: {self.tempo_maximo_espera_envio_segundos}s"
        )

        self._thread_coleta.start()
        self._thread_sincronizacao.start()

    def parar(self) -> None:
        """Solicita parada das threads e aguarda encerramento limpo."""
        self._evento_parada.set()

        if self._thread_coleta and self._thread_coleta.is_alive():
            self._thread_coleta.join(timeout=5)

        if self._thread_sincronizacao and self._thread_sincronizacao.is_alive():
            self._thread_sincronizacao.join(timeout=5)

        print("Orquestrador encerrado.")

    def _loop_coleta(self) -> None:
        """Gera e persiste uma nova medição a cada intervalo configurado."""
        while not self._evento_parada.wait(self.intervalo_medicao_segundos):
            pulsos = next(self._ciclo_pulsos)
            medicao = self.coletor.gerar_medicao(pulsos)
            id_criado = self.repositorio.inserir_medicao(medicao)

            print(
                "[COLETA] "
                f"ID={id_criado} | data_hora={medicao.data_hora} | "
                f"pulsos={medicao.pulsos} | "
                f"intervalo={medicao.chuva_intervalo_mm:.2f} mm | "
                f"acumulado={medicao.chuva_acumulada_mm:.2f} mm"
            )

    def _loop_sincronizacao(self) -> None:
        """Verifica continuamente se já é hora de disparar uma sincronização."""
        self._tentar_sincronizacao_inicial_de_pendencias()

        while not self._evento_parada.is_set():
            try:
                pendentes = self.repositorio.contar_pendentes()

                if pendentes > 0:
                    idade_pendente_mais_antigo = self._idade_segundos_do_pendente_mais_antigo()

                    if pendentes >= self.limite_lote:
                        self._executar_sincronizacao(
                            motivo=f"{pendentes} pendência(s), atingindo o limite do lote"
                        )
                    elif (
                        idade_pendente_mais_antigo is not None
                        and idade_pendente_mais_antigo >= self.tempo_maximo_espera_envio_segundos
                    ):
                        self._executar_sincronizacao(
                            motivo=(
                                "pendente mais antigo aguardando "
                                f"{idade_pendente_mais_antigo:.1f}s"
                            )
                        )

            except Exception as erro:
                print(f"[SINCRONIZAÇÃO] Erro inesperado no loop: {erro}")

            if self._evento_parada.wait(self.intervalo_verificacao_pendencias_segundos):
                break

    def _tentar_sincronizacao_inicial_de_pendencias(self) -> None:
        """
        Ao iniciar o sistema, tenta enviar imediatamente pendências já existentes no banco.
        Isso segue a regra arquitetural definida para retomada após reinício.
        """
        pendentes = self.repositorio.contar_pendentes()

        if pendentes > 0:
            self._executar_sincronizacao(
                motivo=f"sistema iniciado com {pendentes} pendência(s) anterior(es)"
            )

    def _executar_sincronizacao(self, motivo: str) -> None:
        """Executa uma tentativa única de sincronização e imprime o resumo."""
        print(f"[SINCRONIZAÇÃO] Disparando envio por motivo: {motivo}")
        resultado = self.sincronizador.sincronizar_uma_vez()

        print(
            "[SINCRONIZAÇÃO] "
            f"lote_encontrado={resultado['lote_encontrado']} | "
            f"confirmados={resultado['ids_confirmados']} | "
            f"nao_confirmados={resultado['ids_nao_confirmados']} | "
            f"erro={resultado['erro']}"
        )

    def _idade_segundos_do_pendente_mais_antigo(self) -> Optional[float]:
        """Calcula há quantos segundos o pendente mais antigo aguarda sincronização."""
        pendente = self.repositorio.buscar_pendente_mais_antigo()

        if pendente is None:
            return None

        criado_em = datetime.strptime(pendente.criado_em, "%Y-%m-%d %H:%M:%S")
        diferenca = datetime.now() - criado_em
        return diferenca.total_seconds()

    def _validar_configuracao(self) -> None:
        """Valida os parâmetros mínimos necessários para execução contínua."""
        if not self._padrao_pulsos:
            raise ValueError("O padrão de pulsos simulados não pode ser vazio.")

        if self.intervalo_medicao_segundos <= 0:
            raise ValueError("O intervalo de medição deve ser maior que zero.")

        if self.intervalo_verificacao_pendencias_segundos <= 0:
            raise ValueError("O intervalo de verificação deve ser maior que zero.")

        if self.limite_lote <= 0:
            raise ValueError("O limite do lote deve ser maior que zero.")

        if self.tempo_maximo_espera_envio_segundos <= 0:
            raise ValueError("O tempo máximo de espera deve ser maior que zero.")