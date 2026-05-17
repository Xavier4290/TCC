from typing import Dict, List

from .config import LIMITE_LOTE_SINCRONIZACAO
from .repositorio_medicoes import RepositorioMedicoesSQLite
from .cliente_envio import ClienteEnvioSocket


class SincronizadorMedicoes:
    """Coordena a busca de pendentes, o envio do lote e a atualização do banco local."""

    def __init__(
        self,
        repositorio: RepositorioMedicoesSQLite,
        cliente_envio: ClienteEnvioSocket,
        limite_lote: int = LIMITE_LOTE_SINCRONIZACAO,
    ) -> None:
        self.repositorio = repositorio
        self.cliente_envio = cliente_envio
        self.limite_lote = limite_lote

        if self.limite_lote <= 0:
            raise ValueError("O limite do lote deve ser maior que zero.")

    def sincronizar_uma_vez(self) -> Dict[str, object]:
        """
        Executa uma tentativa única de sincronização.
        Retorna um resumo do que aconteceu para facilitar testes e depuração.
        """
        pendentes = self.repositorio.buscar_pendentes(limite=self.limite_lote)

        if not pendentes:
            return {
                "lote_encontrado": 0,
                "ids_enviados": [],
                "ids_confirmados": [],
                "ids_nao_confirmados": [],
                "erro": None,
            }

        ids_enviados = [medicao.id for medicao in pendentes]

        try:
            ids_confirmados = self.cliente_envio.enviar_lote(pendentes)
        except Exception as erro:
            mensagem_erro = f"Falha no envio do lote: {erro}"
            self.repositorio.registrar_falha_envio(ids_enviados, mensagem_erro)

            return {
                "lote_encontrado": len(pendentes),
                "ids_enviados": ids_enviados,
                "ids_confirmados": [],
                "ids_nao_confirmados": ids_enviados,
                "erro": mensagem_erro,
            }

        ids_confirmados_validos = [
            item for item in ids_confirmados if item in ids_enviados
        ]
        ids_nao_confirmados = [
            item for item in ids_enviados if item not in ids_confirmados_validos
        ]

        if ids_confirmados_validos:
            self.repositorio.marcar_como_enviado(ids_confirmados_validos)

        if ids_nao_confirmados:
            self.repositorio.registrar_falha_envio(
                ids_nao_confirmados,
                "Registro não confirmado pelo PC.",
            )

        return {
            "lote_encontrado": len(pendentes),
            "ids_enviados": ids_enviados,
            "ids_confirmados": ids_confirmados_validos,
            "ids_nao_confirmados": ids_nao_confirmados,
            "erro": None,
        }