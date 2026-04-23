import threading
from datetime import datetime
from typing import Optional

from .coletor_base import ColetorBase
from .config import (
    INTERVALO_MANUTENCAO_LOCAL_SEGUNDOS,
    INTERVALO_MEDICAO_SEGUNDOS,
    INTERVALO_VERIFICACAO_PENDENCIAS_SEGUNDOS,
    LIMITE_LOTE_SINCRONIZACAO,
    TEMPO_MAXIMO_ESPERA_ENVIO_SEGUNDOS,
)
from .manutencao_local import ManutencaoLocal
from .repositorio_medicoes import RepositorioMedicoesSQLite
from .sincronizador import SincronizadorMedicoes


class OrquestradorPluviometria:
    """Executa continuamente a coleta, a sincronização e, opcionalmente, a manutenção local."""

    def __init__(
        self,
        repositorio: RepositorioMedicoesSQLite,
        coletor: ColetorBase,
        sincronizador: SincronizadorMedicoes,
        manutencao_local: Optional[ManutencaoLocal] = None,
        intervalo_medicao_segundos: int = INTERVALO_MEDICAO_SEGUNDOS,
        intervalo_verificacao_pendencias_segundos: int = INTERVALO_VERIFICACAO_PENDENCIAS_SEGUNDOS,
        intervalo_manutencao_local_segundos: int = INTERVALO_MANUTENCAO_LOCAL_SEGUNDOS,
        limite_lote: int = LIMITE_LOTE_SINCRONIZACAO,
        tempo_maximo_espera_envio_segundos: int = TEMPO_MAXIMO_ESPERA_ENVIO_SEGUNDOS,
    ) -> None:
        self.repositorio = repositorio
        self.coletor = coletor
        self.sincronizador = sincronizador
        self.manutencao_local = manutencao_local
        self.intervalo_medicao_segundos = intervalo_medicao_segundos
        self.intervalo_verificacao_pendencias_segundos = intervalo_verificacao_pendencias_segundos
        self.intervalo_manutencao_local_segundos = intervalo_manutencao_local_segundos
        self.limite_lote = limite_lote
        self.tempo_maximo_espera_envio_segundos = tempo_maximo_espera_envio_segundos

        self._evento_parada = threading.Event()
        self._thread_coleta: Optional[threading.Thread] = None
        self._thread_sincronizacao: Optional[threading.Thread] = None
        self._thread_manutencao: Optional[threading.Thread] = None

        self._validar_configuracao()

    def iniciar(self) -> None:
        """Inicializa o banco e inicia as rotinas contínuas."""
        self.repositorio.inicializar_banco()

        self._thread_coleta = threading.Thread(
            target=self._loop_coleta,
            name="thread_coleta",
            daemon=True,
        )
        self._thread_sincronizacao = threading.Thread(
            target=self._loop_sincronizacao,
            name="thread_sincronizacao",
            daemon=True,
        )

        print("Iniciando execução contínua.")
        print("A primeira medição será consolidada após o primeiro intervalo completo.")
        print(
            f"Intervalo de medição: {self.intervalo_medicao_segundos}s | "
            f"Verificação de pendências: {self.intervalo_verificacao_pendencias_segundos}s | "
            f"Lote: até {self.limite_lote} registro(s) | "
            f"Tempo máximo de espera para envio: {self.tempo_maximo_espera_envio_segundos}s"
        )

        self._thread_coleta.start()
        self._thread_sincronizacao.start()

        if self.manutencao_local is not None:
            self._thread_manutencao = threading.Thread(
                target=self._loop_manutencao_local,
                name="thread_manutencao_local",
                daemon=True,
            )
            print(
                f"Manutenção local automática habilitada | "
                f"Intervalo: {self.intervalo_manutencao_local_segundos}s"
            )
            self._thread_manutencao.start()
        else:
            print("Manutenção local automática desabilitada.")

    def parar(self) -> None:
        """Solicita parada das threads e aguarda encerramento limpo."""
        self._evento_parada.set()

        if self._thread_coleta and self._thread_coleta.is_alive():
            self._thread_coleta.join(timeout=5)

        if self._thread_sincronizacao and self._thread_sincronizacao.is_alive():
            self._thread_sincronizacao.join(timeout=5)

        if self._thread_manutencao and self._thread_manutencao.is_alive():
            self._thread_manutencao.join(timeout=5)

        print("Orquestrador encerrado.")

    def _loop_coleta(self) -> None:
        """Gera e persiste uma nova medição a cada intervalo configurado."""
        while not self._evento_parada.wait(self.intervalo_medicao_segundos):
            medicao = self.coletor.coletar_medicao()
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

    def _loop_manutencao_local(self) -> None:
        """Executa periodicamente a manutenção local automática."""
        while not self._evento_parada.wait(self.intervalo_manutencao_local_segundos):
            try:
                if self.manutencao_local is None:
                    continue

                resultado = self.manutencao_local.executar_limpeza_enviados_antigos()

                print(
                    "[MANUTENÇÃO] "
                    f"retencao_horas={resultado['retencao_horas']} | "
                    f"data_limite={resultado['data_limite']} | "
                    f"removidos={resultado['removidos']}"
                )

            except Exception as erro:
                print(f"[MANUTENÇÃO] Erro inesperado no loop: {erro}")

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

        criado_em = pendente.criado_em
        diferenca = datetime.now() - criado_em
        
        return diferenca.total_seconds()

    def _validar_configuracao(self) -> None:
        """Valida os parâmetros mínimos necessários para execução contínua."""
        if self.intervalo_medicao_segundos <= 0:
            raise ValueError("O intervalo de medição deve ser maior que zero.")

        if self.intervalo_verificacao_pendencias_segundos <= 0:
            raise ValueError("O intervalo de verificação deve ser maior que zero.")

        if self.intervalo_manutencao_local_segundos <= 0:
            raise ValueError("O intervalo de manutenção local deve ser maior que zero.")

        if self.limite_lote <= 0:
            raise ValueError("O limite do lote deve ser maior que zero.")

        if self.tempo_maximo_espera_envio_segundos <= 0:
            raise ValueError("O tempo máximo de espera deve ser maior que zero.")