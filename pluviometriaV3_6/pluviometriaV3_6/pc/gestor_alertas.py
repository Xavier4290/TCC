from dataclasses import dataclass

from pc.gerador_alertas import ResultadoGeracaoAlerta
from pc.repositorio_alertas_ciclo import RepositorioAlertasCicloSQLite


@dataclass
class ResultadoGestaoAlerta:
    """Representa o resultado operacional da gestão do alerta."""

    acao_executada: str
    alerta_id: int | None
    status_final: str
    nivel_alerta: str
    mensagem: str


class GestorAlertas:
    """
    Coordena o ciclo de vida dos alertas.

    Regras desta primeira versão:
    - se não houver alerta ativo e surgir um alerta persistível -> abrir;
    - se já houver alerta ativo e o evento continuar -> atualizar;
    - se não houver mais motivo para persistir -> encerrar.
    """

    def __init__(self, repositorio: RepositorioAlertasCicloSQLite) -> None:
        self.repositorio = repositorio

    def processar_resultado_alerta(
        self,
        id_ultima_medicao_origem: int,
        data_hora_ultima_medicao: str,
        resultado_alerta: ResultadoGeracaoAlerta,
    ) -> ResultadoGestaoAlerta:
        """Aplica a regra de abertura, atualização ou encerramento do alerta."""
        alerta_ativo = self.repositorio.buscar_alerta_ativo()

        if resultado_alerta.deve_persistir:
            if alerta_ativo is None:
                alerta_id = self.repositorio.abrir_alerta(
                    id_ultima_medicao_origem=id_ultima_medicao_origem,
                    data_hora_ultima_medicao=data_hora_ultima_medicao,
                    resultado_alerta=resultado_alerta,
                )
                return ResultadoGestaoAlerta(
                    acao_executada="aberto",
                    alerta_id=alerta_id,
                    status_final="ABERTO",
                    nivel_alerta=resultado_alerta.nivel_alerta,
                    mensagem=resultado_alerta.mensagem_alerta,
                )

            self.repositorio.atualizar_alerta(
                alerta_id=int(alerta_ativo["id"]),
                id_ultima_medicao_origem=id_ultima_medicao_origem,
                data_hora_ultima_medicao=data_hora_ultima_medicao,
                resultado_alerta=resultado_alerta,
            )
            return ResultadoGestaoAlerta(
                acao_executada="atualizado",
                alerta_id=int(alerta_ativo["id"]),
                status_final="ATUALIZADO",
                nivel_alerta=resultado_alerta.nivel_alerta,
                mensagem=resultado_alerta.mensagem_alerta,
            )

        if alerta_ativo is None:
            return ResultadoGestaoAlerta(
                acao_executada="nenhuma_acao",
                alerta_id=None,
                status_final="SEM_ALERTA_ATIVO",
                nivel_alerta=resultado_alerta.nivel_alerta,
                mensagem="Nenhum alerta ativo para encerrar.",
            )

        self.repositorio.encerrar_alerta(
            alerta_id=int(alerta_ativo["id"]),
            mensagem_encerramento="Evento encerrado por ausência de alerta persistente na janela atual.",
            justificativa_encerramento=resultado_alerta.justificativa_alerta,
        )
        return ResultadoGestaoAlerta(
            acao_executada="encerrado",
            alerta_id=int(alerta_ativo["id"]),
            status_final="ENCERRADO",
            nivel_alerta=resultado_alerta.nivel_alerta,
            mensagem="Alerta encerrado por normalização do cenário.",
        )