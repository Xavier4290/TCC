from dataclasses import dataclass

from .features_chuva import FeaturesChuva


ORDEM_INTENSIDADE = [
    "sem_chuva",
    "leve",
    "moderada",
    "forte",
    "muito_intensa",
]


@dataclass
class ResultadoClassificacaoChuva:
    """Representa a saída analítica inicial do motor de regras."""

    classificacao_chuva: str
    severidade_operacional: str
    tendencia_final: str
    sinal_pre_alerta: str
    alerta_recomendado: str
    score_confianca: float
    justificativa_resumida: str


def classificar_chuva(features: FeaturesChuva) -> ResultadoClassificacaoChuva:
    """Classifica a chuva com base em regras heurísticas sobre as features calculadas."""
    classificacao_base = _classificacao_base_por_taxa(features)
    classificacao_ajustada = _ajustar_classificacao_por_persistencia_e_atividade(
        classificacao_base,
        features,
    )

    severidade = _classificar_severidade(features, classificacao_ajustada)
    sinal_pre_alerta = _classificar_pre_alerta(features)
    alerta_recomendado = _classificar_alerta_recomendado(severidade)
    score_confianca = _calcular_score_confianca(features, classificacao_ajustada)
    justificativa = _montar_justificativa(features, classificacao_ajustada, severidade)

    return ResultadoClassificacaoChuva(
        classificacao_chuva=classificacao_ajustada,
        severidade_operacional=severidade,
        tendencia_final=features.direcao_tendencia,
        sinal_pre_alerta=sinal_pre_alerta,
        alerta_recomendado=alerta_recomendado,
        score_confianca=score_confianca,
        justificativa_resumida=justificativa,
    )


def _classificacao_base_por_taxa(features: FeaturesChuva) -> str:
    """
    Classificação inicial baseada na taxa equivalente.
    Esta etapa é posteriormente ajustada por persistência e atividade.
    """
    if features.chuva_total_mm <= 0 or features.intervalos_com_chuva == 0:
        return "sem_chuva"

    taxa = features.taxa_equivalente_mm_h

    if taxa < 2.5:
        return "leve"
    if taxa < 10:
        return "moderada"
    if taxa < 50:
        return "forte"
    return "muito_intensa"


def _ajustar_classificacao_por_persistencia_e_atividade(
    classificacao_base: str,
    features: FeaturesChuva,
) -> str:
    """
    Ajusta a classificação base usando persistência e atividade imediata.
    A intenção é impedir que janelas curtas e muito intermitentes
    exagerem a intensidade final.
    """
    classificacao = classificacao_base

    if classificacao == "sem_chuva":
        return classificacao

    # Penalizações graduais para chuva pouco persistente.
    if features.percentual_intervalos_com_chuva < 0.75:
        classificacao = _reduzir_nivel(classificacao)

    if features.percentual_intervalos_com_chuva < 0.60:
        classificacao = _reduzir_nivel(classificacao)

    if features.consecutivos_finais_com_chuva <= 1:
        classificacao = _reduzir_nivel(classificacao)

    if features.indice_atividade_imediata < 0.35:
        classificacao = _reduzir_nivel(classificacao)

    # Cenários muito intermitentes têm teto de intensidade.
    if (
        features.percentual_intervalos_com_chuva <= 0.50
        or features.consecutivos_finais_com_chuva <= 1
    ):
        classificacao = _aplicar_teto(classificacao, "moderada")

    elif (
        features.percentual_intervalos_com_chuva < 0.75
        or features.consecutivos_finais_com_chuva < 3
    ):
        classificacao = _aplicar_teto(classificacao, "forte")

    # Cenário muito consistente: mantém classificação alta.
    if (
        features.percentual_intervalos_com_chuva >= 0.80
        and features.consecutivos_finais_com_chuva >= 3
        and features.indice_atividade_imediata >= 0.60
        and features.direcao_tendencia == "alta"
    ):
        return classificacao
    # Se houve chuva real na janela, a classificação final não pode cair para sem_chuva.
    if features.chuva_total_mm > 0 and features.intervalos_com_chuva > 0:
        classificacao = _aplicar_piso(classificacao, "leve")
    return classificacao


def _classificar_severidade(features: FeaturesChuva, classificacao_chuva: str) -> str:
    """Determina a severidade operacional a partir da intensidade e do contexto recente."""
    if classificacao_chuva == "sem_chuva":
        return "observacao"

    if classificacao_chuva == "leve":
        if features.indice_atividade_imediata >= 0.35:
            return "atencao"
        return "observacao"

    if classificacao_chuva == "moderada":
        if (
            features.direcao_tendencia == "alta"
            and features.percentual_intervalos_com_chuva >= 0.67
            and features.consecutivos_finais_com_chuva >= 2
            and features.indice_atividade_imediata >= 0.35
        ):
            return "alerta"
        return "atencao"

    if classificacao_chuva == "forte":
        if (
            features.percentual_intervalos_com_chuva >= 0.80
            and features.consecutivos_finais_com_chuva >= 3
            and features.indice_atividade_imediata >= 0.60
        ):
            return "critico"
        return "alerta"

    # muito_intensa
    if (
        features.percentual_intervalos_com_chuva >= 0.80
        and features.consecutivos_finais_com_chuva >= 3
    ):
        return "critico"

    return "alerta"


def _classificar_pre_alerta(features: FeaturesChuva) -> str:
    """Determina um sinal precoce baseado na atividade imediata e na tendência."""
    if features.indice_atividade_imediata < 0.10 and features.intervalos_com_chuva == 0:
        return "sem_sinal"

    if features.indice_atividade_imediata < 0.25:
        return "atividade_inicial"

    if features.indice_atividade_imediata < 0.60:
        return "intensificacao_em_observacao"

    if features.direcao_tendencia == "alta":
        return "pre_alerta"

    return "intensificacao_em_observacao"


def _classificar_alerta_recomendado(severidade: str) -> str:
    """Traduz a severidade em uma recomendação operacional simples."""
    if severidade == "observacao":
        return "sem_alerta"
    if severidade == "atencao":
        return "monitorar"
    if severidade == "alerta":
        return "alerta_moderado"
    return "alerta_alto"


def _calcular_score_confianca(
    features: FeaturesChuva,
    classificacao_chuva: str,
) -> float:
    """
    Calcula um score heurístico de confiança entre 0 e 1.
    Nesta fase, ele não é probabilidade calibrada, e sim um índice operacional.
    """
    cobertura_janela = min(features.janela_total_segundos / 300, 1.0)

    persistencia = max(
        features.percentual_intervalos_com_chuva,
        features.consecutivos_finais_com_chuva / max(features.quantidade_medicoes, 1),
    )

    confianca_taxa = _calcular_confianca_taxa(features.taxa_equivalente_mm_h)

    if classificacao_chuva == "sem_chuva":
        score = (0.5 * cobertura_janela) + (0.5 * (1 - features.indice_atividade_imediata))
    else:
        score = (
            0.4 * cobertura_janela
            + 0.35 * persistencia
            + 0.25 * confianca_taxa
        )

        # Penalização extra para cenários pouco persistentes.
        if features.percentual_intervalos_com_chuva < 0.60:
            score -= 0.08

        if features.consecutivos_finais_com_chuva <= 1:
            score -= 0.07

        if features.indice_atividade_imediata < 0.35:
            score -= 0.05

    return round(max(0.0, min(score, 1.0)), 3)


def _calcular_confianca_taxa(taxa_equivalente_mm_h: float) -> float:
    """Mede quão distante a taxa está dos limiares principais da classificação."""
    if taxa_equivalente_mm_h <= 0:
        return 1.0

    limiares = [2.5, 10.0, 50.0]
    menor_distancia = min(abs(taxa_equivalente_mm_h - limiar) for limiar in limiares)

    normalizada = min(menor_distancia / 10.0, 1.0)
    return round(0.2 + (0.8 * normalizada), 3)


def _montar_justificativa(
    features: FeaturesChuva,
    classificacao_chuva: str,
    severidade: str,
) -> str:
    """Gera um resumo textual simples do porquê da decisão."""
    return (
        f"classificacao={classificacao_chuva}; "
        f"severidade={severidade}; "
        f"taxa_mm_h={features.taxa_equivalente_mm_h}; "
        f"atividade={features.indice_atividade_imediata}; "
        f"persistencia={features.percentual_intervalos_com_chuva}; "
        f"consecutivos_finais={features.consecutivos_finais_com_chuva}; "
        f"tendencia={features.direcao_tendencia}"
    )


def _reduzir_nivel(classificacao: str) -> str:
    """Reduz a classificação em um nível, respeitando o limite mínimo."""
    indice = ORDEM_INTENSIDADE.index(classificacao)
    novo_indice = max(indice - 1, 0)
    return ORDEM_INTENSIDADE[novo_indice]


def _aplicar_teto(classificacao: str, teto: str) -> str:
    """Aplica um teto máximo para a classificação."""
    indice_classificacao = ORDEM_INTENSIDADE.index(classificacao)
    indice_teto = ORDEM_INTENSIDADE.index(teto)

    if indice_classificacao > indice_teto:
        return ORDEM_INTENSIDADE[indice_teto]

    return classificacao


def _aplicar_piso(classificacao: str, piso: str) -> str:
    """Aplica um piso mínimo para a classificação."""
    indice_classificacao = ORDEM_INTENSIDADE.index(classificacao)
    indice_piso = ORDEM_INTENSIDADE.index(piso)

    if indice_classificacao < indice_piso:
        return ORDEM_INTENSIDADE[indice_piso]

    return classificacao