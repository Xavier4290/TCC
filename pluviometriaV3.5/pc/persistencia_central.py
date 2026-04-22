from typing import List

from .processador_analitico import ProcessadorAnaliticoCentral
from .repositorio_alertas_ciclo import RepositorioAlertasCicloSQLite
from .repositorio_analitico import RepositorioAnaliticoSQLite
from .repositorio_central import RepositorioCentralSQLite


class PersistenciaCentralSQLite:
    """
    Persistência central real do lado do PC.
    Valida os registros recebidos, grava em SQLite e, em seguida,
    tenta executar a análise automática da janela recente, incluindo
    a gestão do ciclo de vida dos alertas.
    """

    def __init__(
        self,
        repositorio: RepositorioCentralSQLite | None = None,
        repositorio_analitico: RepositorioAnaliticoSQLite | None = None,
        repositorio_alertas_ciclo: RepositorioAlertasCicloSQLite | None = None,
        processador_analitico: ProcessadorAnaliticoCentral | None = None,
    ) -> None:
        self.repositorio = repositorio or RepositorioCentralSQLite()
        self.repositorio.inicializar_banco()

        self.repositorio_analitico = repositorio_analitico or RepositorioAnaliticoSQLite()
        self.repositorio_analitico.inicializar_banco()

        self.repositorio_alertas_ciclo = repositorio_alertas_ciclo or RepositorioAlertasCicloSQLite()
        self.repositorio_alertas_ciclo.inicializar_banco()

        self.processador_analitico = processador_analitico or ProcessadorAnaliticoCentral(
            repositorio_central=self.repositorio,
            repositorio_analitico=self.repositorio_analitico,
            repositorio_alertas_ciclo=self.repositorio_alertas_ciclo,
        )

    def processar_lote(self, medicoes: List[dict]) -> List[int]:
        """
        Valida cada registro recebido e retorna a lista de IDs confirmados.
        Registros duplicados já persistidos também são confirmados.
        Após a persistência bruta, tenta executar a análise automática.
        """
        ids_confirmados = []

        for medicao in medicoes:
            if self._registro_valido(medicao):
                if self.repositorio.inserir_ou_confirmar_medicao(medicao):
                    ids_confirmados.append(medicao["id"])

        if ids_confirmados:
            self._tentar_processar_analise()

        return ids_confirmados

    def _tentar_processar_analise(self) -> None:
        """
        Tenta executar a análise automática sem comprometer a confirmação
        dos dados brutos já persistidos.
        """
        try:
            resultado = self.processador_analitico.processar_ultima_janela()

            if resultado.get("analise_executada"):
                print(
                    "[ANALITICA] "
                    f"id_ultima={resultado['id_ultima_medicao_origem']} | "
                    f"classificacao={resultado['classificacao_chuva']} | "
                    f"severidade={resultado['severidade_operacional']} | "
                    f"tendencia={resultado['tendencia_final']} | "
                    f"confianca={resultado['score_confianca']} | "
                    f"analise_persistida_ou_confirmada={resultado['analise_persistida_ou_confirmada']}"
                )

                print(
                    "[ALERTA] "
                    f"nivel={resultado['nivel_alerta']} | "
                    f"deve_persistir={resultado['alerta_deve_persistir']} | "
                    f"acao={resultado['acao_alerta']} | "
                    f"alerta_id={resultado['alerta_id']} | "
                    f"status_final={resultado['status_alerta_final']} | "
                    f"mensagem={resultado['mensagem_alerta']}"
                )
            else:
                print(f"[ANALITICA] {resultado['motivo']}")

        except Exception as erro:
            print(f"[ANALITICA] Falha ao processar a análise automática: {erro}")

    def _registro_valido(self, medicao: dict) -> bool:
        """Aplica validações básicas para aceitar ou rejeitar um registro."""
        if not isinstance(medicao, dict):
            return False

        campos_obrigatorios = [
            "id",
            "data_hora",
            "pulsos",
            "chuva_intervalo_mm",
            "chuva_acumulada_mm",
        ]

        for campo in campos_obrigatorios:
            if campo not in medicao:
                return False

        if not isinstance(medicao["id"], int) or medicao["id"] <= 0:
            return False

        if not isinstance(medicao["data_hora"], str) or not medicao["data_hora"].strip():
            return False

        if not isinstance(medicao["pulsos"], int) or medicao["pulsos"] < 0:
            return False

        if not isinstance(medicao["chuva_intervalo_mm"], (int, float)):
            return False

        if not isinstance(medicao["chuva_acumulada_mm"], (int, float)):
            return False

        if medicao["chuva_intervalo_mm"] < 0 or medicao["chuva_acumulada_mm"] < 0:
            return False

        return True