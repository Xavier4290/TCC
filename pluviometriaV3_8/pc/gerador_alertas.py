from dataclasses import dataclass

from pc.analisador_evento import ResultadoAnaliseEvento


@dataclass
class ResultadoGeracaoAlerta:
    """Representa a saída da camada de geração de alertas."""

    nivel_alerta: str
    deve_persistir: bool
    mensagem_alerta: str
    justificativa_alerta: str


def gerar_alerta(resultado_analise: ResultadoAnaliseEvento) -> ResultadoGeracaoAlerta:
    """
    Traduz a análise em um evento operacional simples.
    Nesta primeira versão, a lógica é totalmente heurística.
    """
    classificacao = resultado_analise.classificacao.classificacao_chuva
    severidade = resultado_analise.classificacao.severidade_operacional
    tendencia = resultado_analise.classificacao.tendencia_final
    sinal_pre_alerta = resultado_analise.classificacao.sinal_pre_alerta
    confianca = resultado_analise.classificacao.score_confianca

    if classificacao == "sem_chuva":
        return ResultadoGeracaoAlerta(
            nivel_alerta="sem_alerta",
            deve_persistir=False,
            mensagem_alerta="Sem chuva relevante para emissão de alerta.",
            justificativa_alerta=_montar_justificativa(
                classificacao, severidade, tendencia, sinal_pre_alerta, confianca
            ),
        )

    if severidade == "observacao":
        if sinal_pre_alerta == "pre_alerta" and confianca >= 0.45:
            return ResultadoGeracaoAlerta(
                nivel_alerta="pre_alerta",
                deve_persistir=True,
                mensagem_alerta=(
                    "Sinal precoce de intensificação detectado. "
                    "Recomenda-se monitoramento reforçado."
                ),
                justificativa_alerta=_montar_justificativa(
                    classificacao, severidade, tendencia, sinal_pre_alerta, confianca
                ),
            )

        return ResultadoGeracaoAlerta(
            nivel_alerta="sem_alerta",
            deve_persistir=False,
            mensagem_alerta="Cenário em observação sem necessidade de alerta formal.",
            justificativa_alerta=_montar_justificativa(
                classificacao, severidade, tendencia, sinal_pre_alerta, confianca
            ),
        )

    if severidade == "atencao":
        return ResultadoGeracaoAlerta(
            nivel_alerta="atencao",
            deve_persistir=True,
            mensagem_alerta=(
                "Chuva em nível de atenção. "
                "Manter monitoramento e acompanhamento da tendência."
            ),
            justificativa_alerta=_montar_justificativa(
                classificacao, severidade, tendencia, sinal_pre_alerta, confianca
            ),
        )

    if severidade == "alerta":
        return ResultadoGeracaoAlerta(
            nivel_alerta="alerta_moderado",
            deve_persistir=True,
            mensagem_alerta=(
                "Condição de alerta detectada. "
                "Recomenda-se prontidão operacional e acompanhamento intensivo."
            ),
            justificativa_alerta=_montar_justificativa(
                classificacao, severidade, tendencia, sinal_pre_alerta, confianca
            ),
        )

    return ResultadoGeracaoAlerta(
        nivel_alerta="alerta_alto",
        deve_persistir=True,
        mensagem_alerta=(
            "Condição crítica detectada. "
            "Recomenda-se resposta prioritária e atenção imediata."
        ),
        justificativa_alerta=_montar_justificativa(
            classificacao, severidade, tendencia, sinal_pre_alerta, confianca
        ),
    )


def _montar_justificativa(
    classificacao: str,
    severidade: str,
    tendencia: str,
    sinal_pre_alerta: str,
    confianca: float,
) -> str:
    """Monta uma justificativa resumida para o alerta gerado."""
    return (
        f"classificacao={classificacao}; "
        f"severidade={severidade}; "
        f"tendencia={tendencia}; "
        f"pre_alerta={sinal_pre_alerta}; "
        f"confianca={confianca}"
    )