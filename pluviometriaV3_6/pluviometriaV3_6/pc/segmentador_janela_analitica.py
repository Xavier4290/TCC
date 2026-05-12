from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from app.config import (
    INTERVALO_MEDICAO_SEGUNDOS,
    PERMITIR_REINICIO_ACUMULADO_NA_JANELA,
    TOLERANCIA_CONTIGUIDADE_MEDICOES_SEGUNDOS,
)
from app.modelos import Medicao


FORMATO_DATA = "%Y-%m-%d %H:%M:%S"


@dataclass
class ResultadoSegmentacaoJanela:
    """Representa o resultado da seleção de uma janela analítica válida."""

    medicoes_segmentadas: list[Medicao]
    segmento_valido: bool
    motivo: str


def segmentar_janela_analitica(
    medicoes: Sequence[Medicao],
    intervalo_medicao_segundos: int = INTERVALO_MEDICAO_SEGUNDOS,
    tolerancia_segundos: int = TOLERANCIA_CONTIGUIDADE_MEDICOES_SEGUNDOS,
    permitir_reinicio_acumulado: bool = PERMITIR_REINICIO_ACUMULADO_NA_JANELA,
) -> ResultadoSegmentacaoJanela:
    """
    Seleciona, a partir do fim da lista, o trecho mais recente de medições que
    ainda forma uma janela contínua e coerente para análise.
    """
    if not medicoes:
        return ResultadoSegmentacaoJanela(
            medicoes_segmentadas=[],
            segmento_valido=False,
            motivo="nenhuma medição disponível",
        )

    if intervalo_medicao_segundos <= 0:
        raise ValueError("O intervalo de medição deve ser maior que zero.")

    if tolerancia_segundos < 0:
        raise ValueError("A tolerância de continuidade não pode ser negativa.")

    segmento = [medicoes[-1]]
    motivo_quebra = "janela contínua"

    esperado_maximo = intervalo_medicao_segundos + tolerancia_segundos

    for indice in range(len(medicoes) - 2, -1, -1):
        anterior = medicoes[indice]
        atual_segmento = segmento[0]

        diferenca_segundos = _diferenca_segundos(anterior.data_hora, atual_segmento.data_hora)

        if diferenca_segundos > esperado_maximo:
            motivo_quebra = (
                f"quebra de continuidade temporal: intervalo de {diferenca_segundos}s "
                f"entre {anterior.data_hora} e {atual_segmento.data_hora}"
            )
            break

        if (
            not permitir_reinicio_acumulado
            and anterior.chuva_acumulada_mm > atual_segmento.chuva_acumulada_mm
        ):
            motivo_quebra = (
                "reinício de acumulado detectado entre "
                f"{anterior.data_hora} e {atual_segmento.data_hora}"
            )
            break

        segmento.insert(0, anterior)

    if len(segmento) < 2:
        return ResultadoSegmentacaoJanela(
            medicoes_segmentadas=segmento,
            segmento_valido=False,
            motivo=f"janela curta demais: {len(segmento)} medição(ões)",
        )

    return ResultadoSegmentacaoJanela(
        medicoes_segmentadas=segmento,
        segmento_valido=True,
        motivo=motivo_quebra,
    )


def _diferenca_segundos(data_hora_anterior: str, data_hora_posterior: str) -> int:
    """Calcula a diferença em segundos entre dois timestamps."""
    anterior = datetime.strptime(data_hora_anterior, FORMATO_DATA)
    posterior = datetime.strptime(data_hora_posterior, FORMATO_DATA)
    return int((posterior - anterior).total_seconds())