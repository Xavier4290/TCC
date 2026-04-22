from dataclasses import dataclass
from typing import Sequence

from pc.classificador_chuva import ResultadoClassificacaoChuva, classificar_chuva
from pc.features_chuva import FeaturesChuva, extrair_features_chuva


@dataclass
class ResultadoAnaliseEvento:
    """Representa a análise consolidada de um evento de chuva."""

    features: FeaturesChuva
    classificacao: ResultadoClassificacaoChuva


def analisar_evento_chuva(medicoes: Sequence[object]) -> ResultadoAnaliseEvento:
    """
    Executa a análise completa de um conjunto de medições:
    1. extrai features;
    2. classifica o cenário;
    3. devolve o resultado consolidado.
    """
    features = extrair_features_chuva(medicoes)
    classificacao = classificar_chuva(features)

    return ResultadoAnaliseEvento(
        features=features,
        classificacao=classificacao,
    )