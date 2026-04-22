from typing import Dict

from app.config import LIMITE_JANELA_ANALITICA, MINIMO_MEDICOES_ANALISE
from app.modelos import Medicao
from pc.analisador_evento import analisar_evento_chuva
from pc.gerador_alertas import gerar_alerta
from pc.gestor_alertas import GestorAlertas
from pc.repositorio_alertas_ciclo import RepositorioAlertasCicloSQLite
from pc.repositorio_analitico import RepositorioAnaliticoSQLite
from pc.repositorio_central import RepositorioCentralSQLite
from pc.segmentador_janela_analitica import segmentar_janela_analitica


class ProcessadorAnaliticoCentral:
    """
    Coordena a análise automática no lado do PC após a persistência bruta.

    Fluxo:
    1. busca a janela recente no banco central;
    2. segmenta o trecho contínuo mais recente;
    3. verifica se há medições suficientes;
    4. executa a análise;
    5. persiste o resultado analítico;
    6. gera alerta;
    7. delega ao gestor a abertura, atualização ou encerramento do alerta.
    """

    def __init__(
        self,
        repositorio_central: RepositorioCentralSQLite,
        repositorio_analitico: RepositorioAnaliticoSQLite,
        repositorio_alertas_ciclo: RepositorioAlertasCicloSQLite,
        limite_janela: int = LIMITE_JANELA_ANALITICA,
        minimo_medicoes: int = MINIMO_MEDICOES_ANALISE,
    ) -> None:
        self.repositorio_central = repositorio_central
        self.repositorio_analitico = repositorio_analitico
        self.repositorio_alertas_ciclo = repositorio_alertas_ciclo
        self.gestor_alertas = GestorAlertas(self.repositorio_alertas_ciclo)
        self.limite_janela = limite_janela
        self.minimo_medicoes = minimo_medicoes
        self._validar_configuracao()

    def processar_ultima_janela(self) -> Dict[str, object]:
        """
        Executa a análise da janela mais recente, persiste o resultado analítico
        e aplica o ciclo de vida do alerta correspondente.
        """
        registros_brutos = self.repositorio_central.listar_ultimas_medicoes_brutas(
            limite=self.limite_janela
        )

        if len(registros_brutos) < self.minimo_medicoes:
            return {
                "analise_executada": False,
                "motivo": (
                    f"janela insuficiente: {len(registros_brutos)} medição(ões), "
                    f"mínimo necessário = {self.minimo_medicoes}"
                ),
            }

        medicoes = [
            Medicao(
                data_hora=str(registro["data_hora"]),
                pulsos=int(registro["pulsos"]),
                chuva_intervalo_mm=float(registro["chuva_intervalo_mm"]),
                chuva_acumulada_mm=float(registro["chuva_acumulada_mm"]),
            )
            for registro in registros_brutos
        ]

        segmentacao = segmentar_janela_analitica(medicoes)

        if not segmentacao.segmento_valido:
            return {
                "analise_executada": False,
                "motivo": f"segmento inválido: {segmentacao.motivo}",
            }

        if len(segmentacao.medicoes_segmentadas) < self.minimo_medicoes:
            return {
                "analise_executada": False,
                "motivo": (
                    f"segmento recente insuficiente: {len(segmentacao.medicoes_segmentadas)} "
                    f"medição(ões), mínimo necessário = {self.minimo_medicoes}; "
                    f"motivo_segmentacao = {segmentacao.motivo}"
                ),
            }

        resultado = analisar_evento_chuva(segmentacao.medicoes_segmentadas)

        ultima_medicao = segmentacao.medicoes_segmentadas[-1]
        id_ultima = self._obter_id_origem_da_ultima_medicao(
            registros_brutos,
            ultima_medicao.data_hora,
        )

        analise_persistida_ou_confirmada = self.repositorio_analitico.inserir_ou_confirmar_analise(
            id_ultima_medicao_origem=id_ultima,
            data_hora_ultima_medicao=ultima_medicao.data_hora,
            resultado=resultado,
        )

        resultado_alerta = gerar_alerta(resultado)
        resultado_gestao = self.gestor_alertas.processar_resultado_alerta(
            id_ultima_medicao_origem=id_ultima,
            data_hora_ultima_medicao=ultima_medicao.data_hora,
            resultado_alerta=resultado_alerta,
        )

        return {
            "analise_executada": True,
            "id_ultima_medicao_origem": id_ultima,
            "classificacao_chuva": resultado.classificacao.classificacao_chuva,
            "severidade_operacional": resultado.classificacao.severidade_operacional,
            "tendencia_final": resultado.classificacao.tendencia_final,
            "score_confianca": resultado.classificacao.score_confianca,
            "analise_persistida_ou_confirmada": analise_persistida_ou_confirmada,
            "medicoes_na_janela": len(segmentacao.medicoes_segmentadas),
            "nivel_alerta": resultado_alerta.nivel_alerta,
            "alerta_deve_persistir": resultado_alerta.deve_persistir,
            "mensagem_alerta": resultado_alerta.mensagem_alerta,
            "acao_alerta": resultado_gestao.acao_executada,
            "alerta_id": resultado_gestao.alerta_id,
            "status_alerta_final": resultado_gestao.status_final,
        }

    def _obter_id_origem_da_ultima_medicao(
        self,
        registros_brutos: list[dict],
        data_hora_ultima_medicao: str,
    ) -> int:
        """Localiza o id_origem correspondente à última medição da janela segmentada."""
        for registro in reversed(registros_brutos):
            if str(registro["data_hora"]) == data_hora_ultima_medicao:
                return int(registro["id_origem"])

        raise RuntimeError(
            "Não foi possível localizar o id_origem da última medição da janela segmentada."
        )

    def _validar_configuracao(self) -> None:
        """Valida os parâmetros básicos da janela analítica."""
        if self.limite_janela <= 0:
            raise ValueError("O limite da janela analítica deve ser maior que zero.")

        if self.minimo_medicoes <= 0:
            raise ValueError("O mínimo de medições para análise deve ser maior que zero.")

        if self.minimo_medicoes > self.limite_janela:
            raise ValueError(
                "O mínimo de medições para análise não pode ser maior que o limite da janela."
            )