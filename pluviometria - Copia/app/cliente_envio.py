import json
import socket
from typing import List

from .config import HOST_SERVIDOR_PC, PORTA_SERVIDOR_PC, TIMEOUT_SOCKET_SEGUNDOS
from .modelos import MedicaoPersistida


class ClienteEnvioSocket:
    """Responsável por enviar um lote JSON ao servidor do PC e interpretar a resposta."""

    def __init__(
        self,
        host: str = HOST_SERVIDOR_PC,
        porta: int = PORTA_SERVIDOR_PC,
        timeout_segundos: int = TIMEOUT_SOCKET_SEGUNDOS,
    ) -> None:
        self.host = host
        self.porta = porta
        self.timeout_segundos = timeout_segundos

    def enviar_lote(self, medicoes: List[MedicaoPersistida]) -> List[int]:
        """
        Envia um lote de medições ao servidor e retorna os IDs confirmados pelo PC.
        Lança exceção em caso de falha de rede ou resposta inválida.
        """
        if not medicoes:
            return []

        carga_bytes = self._montar_payload_json(medicoes)
        resposta_bytes = self._executar_requisicao(carga_bytes)
        return self._interpretar_resposta(resposta_bytes)

    def _montar_payload_json(self, medicoes: List[MedicaoPersistida]) -> bytes:
        """Converte o lote em JSON no formato acordado para sincronização."""
        payload = {
            "medicoes": [
                {
                    "id": medicao.id,
                    "data_hora": medicao.data_hora,
                    "pulsos": medicao.pulsos,
                    "chuva_intervalo_mm": medicao.chuva_intervalo_mm,
                    "chuva_acumulada_mm": medicao.chuva_acumulada_mm,
                }
                for medicao in medicoes
            ]
        }

        texto_json = json.dumps(payload, ensure_ascii=False)
        return texto_json.encode("utf-8")

    def _executar_requisicao(self, carga_bytes: bytes) -> bytes:
        """Abre conexão TCP, envia o payload completo e lê a resposta do servidor."""
        with socket.create_connection(
            (self.host, self.porta), timeout=self.timeout_segundos
        ) as cliente:
            cliente.settimeout(self.timeout_segundos)
            cliente.sendall(carga_bytes)

            # Informa ao servidor que o envio terminou.
            cliente.shutdown(socket.SHUT_WR)

            resposta = bytearray()

            while True:
                trecho = cliente.recv(4096)
                if not trecho:
                    break
                resposta.extend(trecho)

        if not resposta:
            raise RuntimeError("O servidor não retornou resposta.")

        return bytes(resposta)

    def _interpretar_resposta(self, resposta_bytes: bytes) -> List[int]:
        """Valida o JSON de resposta e extrai os IDs confirmados."""
        try:
            resposta = json.loads(resposta_bytes.decode("utf-8"))
        except json.JSONDecodeError as erro:
            raise RuntimeError(f"Resposta JSON inválida do servidor: {erro}") from erro

        status = resposta.get("status")
        mensagem = resposta.get("mensagem", "")
        ids_recebidos = resposta.get("ids_recebidos", [])

        if status not in {"ok", "parcial", "erro"}:
            raise RuntimeError("O servidor retornou um status desconhecido.")

        if not isinstance(ids_recebidos, list):
            raise RuntimeError("O campo ids_recebidos precisa ser uma lista.")

        ids_confirmados = []
        for item in ids_recebidos:
            if isinstance(item, int) and item > 0 and item not in ids_confirmados:
                ids_confirmados.append(item)

        if status == "erro":
            detalhe = mensagem or "O servidor rejeitou o lote enviado."
            raise RuntimeError(detalhe)

        return ids_confirmados