from typing import Dict, List


class PersistenciaCentralSimulada:
    """
    Simula a persistência central no PC.
    Nesta etapa, os registros válidos são guardados apenas em memória.
    """

    def __init__(self) -> None:
        self.registros_por_id: Dict[int, dict] = {}

    def processar_lote(self, medicoes: List[dict]) -> List[int]:
        """
        Valida cada registro recebido e retorna a lista de IDs aceitos.
        Registros inválidos são ignorados.
        """
        ids_confirmados = []

        for medicao in medicoes:
            if self._registro_valido(medicao):
                registro_id = medicao["id"]
                self.registros_por_id[registro_id] = medicao
                ids_confirmados.append(registro_id)

        return ids_confirmados

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