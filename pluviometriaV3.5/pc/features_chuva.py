from dataclasses import dataclass
from typing import Sequence

from app.config import INTERVALO_MEDICAO_SEGUNDOS


PULSOS_REFERENCIA_ATIVIDADE = 12


@dataclass
class FeaturesChuva:
    """Representa o conjunto de features calculadas para uma janela de medições."""

    quantidade_medicoes: int
    intervalo_medicao_segundos: int
    janela_total_segundos: int
    pulsos_totais: int
    chuva_total_mm: float
    taxa_equivalente_mm_h: float
    media_pulsos_por_intervalo: float
    media_mm_por_intervalo: float
    max_pulsos_em_intervalo: int
    max_mm_em_intervalo: float
    intervalos_com_chuva: int
    percentual_intervalos_com_chuva: float
    consecutivos_finais_com_chuva: int
    tendencia_taxa_mm_h: float
    direcao_tendencia: str
    indice_atividade_imediata: float


def extrair_features_chuva(
    medicoes: Sequence[object],
    intervalo_medicao_segundos: int = INTERVALO_MEDICAO_SEGUNDOS,
) -> FeaturesChuva:
    """
    Calcula features analíticas a partir de uma sequência de medições.

    Observação importante:
    esta primeira versão trabalha com pulsos agregados por intervalo.
    A análise pulso a pulso poderá ser refinada no futuro quando houver
    armazenamento dos timestamps individuais dos pulsos.
    """
    if not medicoes:
        raise ValueError("É necessário informar ao menos uma medição.")

    if intervalo_medicao_segundos <= 0:
        raise ValueError("O intervalo de medição deve ser maior que zero.")

    pulsos_por_intervalo = [_obter_inteiro(medicao, "pulsos") for medicao in medicoes]
    chuva_por_intervalo = [
        _obter_float(medicao, "chuva_intervalo_mm") for medicao in medicoes
    ]

    quantidade_medicoes = len(medicoes)
    janela_total_segundos = quantidade_medicoes * intervalo_medicao_segundos

    pulsos_totais = sum(pulsos_por_intervalo)
    chuva_total_mm = round(sum(chuva_por_intervalo), 2)

    taxa_equivalente_mm_h = round(
        (chuva_total_mm / janela_total_segundos) * 3600,
        2,
    )

    media_pulsos_por_intervalo = round(pulsos_totais / quantidade_medicoes, 2)
    media_mm_por_intervalo = round(chuva_total_mm / quantidade_medicoes, 2)

    max_pulsos_em_intervalo = max(pulsos_por_intervalo)
    max_mm_em_intervalo = round(max(chuva_por_intervalo), 2)

    intervalos_com_chuva = sum(1 for valor in chuva_por_intervalo if valor > 0)
    percentual_intervalos_com_chuva = round(
        intervalos_com_chuva / quantidade_medicoes,
        3,
    )

    consecutivos_finais_com_chuva = _calcular_consecutivos_finais_com_chuva(
        chuva_por_intervalo
    )

    tendencia_taxa_mm_h, direcao_tendencia = _calcular_tendencia_taxa_mm_h(
        chuva_por_intervalo,
        intervalo_medicao_segundos,
    )

    indice_atividade_imediata = _calcular_indice_atividade_imediata(
        pulsos_por_intervalo
    )

    return FeaturesChuva(
        quantidade_medicoes=quantidade_medicoes,
        intervalo_medicao_segundos=intervalo_medicao_segundos,
        janela_total_segundos=janela_total_segundos,
        pulsos_totais=pulsos_totais,
        chuva_total_mm=chuva_total_mm,
        taxa_equivalente_mm_h=taxa_equivalente_mm_h,
        media_pulsos_por_intervalo=media_pulsos_por_intervalo,
        media_mm_por_intervalo=media_mm_por_intervalo,
        max_pulsos_em_intervalo=max_pulsos_em_intervalo,
        max_mm_em_intervalo=max_mm_em_intervalo,
        intervalos_com_chuva=intervalos_com_chuva,
        percentual_intervalos_com_chuva=percentual_intervalos_com_chuva,
        consecutivos_finais_com_chuva=consecutivos_finais_com_chuva,
        tendencia_taxa_mm_h=tendencia_taxa_mm_h,
        direcao_tendencia=direcao_tendencia,
        indice_atividade_imediata=indice_atividade_imediata,
    )


def _obter_inteiro(objeto: object, atributo: str) -> int:
    """Lê e valida um campo inteiro de uma medição."""
    valor = getattr(objeto, atributo, None)

    if not isinstance(valor, int):
        raise TypeError(f"O atributo '{atributo}' deve ser inteiro.")

    return valor


def _obter_float(objeto: object, atributo: str) -> float:
    """Lê e valida um campo numérico de uma medição."""
    valor = getattr(objeto, atributo, None)

    if not isinstance(valor, (int, float)):
        raise TypeError(f"O atributo '{atributo}' deve ser numérico.")

    return float(valor)


def _calcular_consecutivos_finais_com_chuva(chuva_por_intervalo: Sequence[float]) -> int:
    """Conta quantos intervalos consecutivos com chuva existem no fim da janela."""
    consecutivos = 0

    for valor in reversed(chuva_por_intervalo):
        if valor > 0:
            consecutivos += 1
        else:
            break

    return consecutivos


def _calcular_tendencia_taxa_mm_h(
    chuva_por_intervalo: Sequence[float],
    intervalo_medicao_segundos: int,
) -> tuple[float, str]:
    """
    Compara a metade mais recente da janela com a metade mais antiga
    e devolve a diferença entre as taxas equivalentes em mm/h.
    """
    quantidade = len(chuva_por_intervalo)

    if quantidade == 1:
        return 0.0, "estável"

    meio = quantidade // 2
    if meio == 0:
        return 0.0, "estável"

    janela_antiga = chuva_por_intervalo[:meio]
    janela_recente = chuva_por_intervalo[meio:]

    if not janela_antiga or not janela_recente:
        return 0.0, "estável"

    taxa_antiga = _taxa_equivalente_mm_h(janela_antiga, intervalo_medicao_segundos)
    taxa_recente = _taxa_equivalente_mm_h(janela_recente, intervalo_medicao_segundos)

    diferenca = round(taxa_recente - taxa_antiga, 2)

    if diferenca > 1.0:
        direcao = "alta"
    elif diferenca < -1.0:
        direcao = "queda"
    else:
        direcao = "estável"

    return diferenca, direcao


def _taxa_equivalente_mm_h(
    chuva_por_intervalo: Sequence[float],
    intervalo_medicao_segundos: int,
) -> float:
    """Calcula a taxa equivalente em mm/h para uma janela qualquer."""
    total_mm = sum(chuva_por_intervalo)
    total_segundos = len(chuva_por_intervalo) * intervalo_medicao_segundos

    if total_segundos <= 0:
        return 0.0

    return (total_mm / total_segundos) * 3600


def _calcular_indice_atividade_imediata(pulsos_por_intervalo: Sequence[int]) -> float:
    """
    Gera um score heurístico de 0 a 1 para atividade imediata.
    Usa os 3 intervalos mais recentes, com maior peso para o mais novo.
    """
    ultimos = list(pulsos_por_intervalo[-3:])

    while len(ultimos) < 3:
        ultimos.insert(0, 0)

    pesos = [0.2, 0.3, 0.5]
    normalizados = [
        min(valor / PULSOS_REFERENCIA_ATIVIDADE, 1.0) for valor in ultimos
    ]

    atividade_ponderada = sum(peso * valor for peso, valor in zip(pesos, normalizados))
    persistencia = min(sum(1 for valor in ultimos if valor > 0) / 3, 1.0)

    indice = (0.7 * atividade_ponderada) + (0.3 * persistencia)
    return round(min(indice, 1.0), 3)