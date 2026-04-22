import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from app.config import CAMINHO_BANCO_CENTRAL_PC
from pc.gerador_alertas import ResultadoGeracaoAlerta


class RepositorioAlertasSQLite:
    """
    Repositório da camada de alertas no banco central do PC.

    Mantém os alertas em tabela separada da análise, preservando a evolução
    arquitetural do projeto e permitindo inspeção operacional independente.
    """

    def __init__(self, caminho_banco: Path | str = CAMINHO_BANCO_CENTRAL_PC) -> None:
        self.caminho_banco = Path(caminho_banco)
        self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)

    def inicializar_banco(self) -> None:
        """Cria a tabela de alertas, caso ainda não exista."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alertas_chuva (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_ultima_medicao_origem INTEGER NOT NULL UNIQUE,
                    data_hora_ultima_medicao TEXT NOT NULL,
                    nivel_alerta TEXT NOT NULL,
                    mensagem_alerta TEXT NOT NULL,
                    justificativa_alerta TEXT NOT NULL,
                    gerado_em TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alertas_chuva_id_ultima
                ON alertas_chuva (id_ultima_medicao_origem)
                """
            )

            conexao.commit()

    def inserir_ou_confirmar_alerta(
        self,
        id_ultima_medicao_origem: int,
        data_hora_ultima_medicao: str,
        resultado_alerta: ResultadoGeracaoAlerta,
    ) -> bool:
        """
        Insere o alerta ou confirma como válido caso ele já exista.
        Apenas alertas com deve_persistir=True devem ser enviados para este método.
        """
        if id_ultima_medicao_origem <= 0:
            raise ValueError("id_ultima_medicao_origem deve ser maior que zero.")

        gerado_em = self._agora_iso()

        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT OR IGNORE INTO alertas_chuva (
                    id_ultima_medicao_origem,
                    data_hora_ultima_medicao,
                    nivel_alerta,
                    mensagem_alerta,
                    justificativa_alerta,
                    gerado_em
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    id_ultima_medicao_origem,
                    data_hora_ultima_medicao,
                    resultado_alerta.nivel_alerta,
                    resultado_alerta.mensagem_alerta,
                    resultado_alerta.justificativa_alerta,
                    gerado_em,
                ),
            )

            conexao.commit()

            if cursor.rowcount == 1:
                return True

        return self.alerta_existe(id_ultima_medicao_origem)

    def alerta_existe(self, id_ultima_medicao_origem: int) -> bool:
        """Verifica se já existe alerta para a medição final informada."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM alertas_chuva
                WHERE id_ultima_medicao_origem = ?
                LIMIT 1
                """,
                (id_ultima_medicao_origem,),
            )
            linha = cursor.fetchone()

        return linha is not None

    def contar_alertas(self) -> int:
        """Retorna a quantidade total de alertas persistidos."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT COUNT(*) FROM alertas_chuva")
            resultado = cursor.fetchone()

        return int(resultado[0])

    def listar_todos(self, limite: int = 100) -> List[Dict[str, object]]:
        """Lista os alertas persistidos."""
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        with sqlite3.connect(self.caminho_banco) as conexao:
            conexao.row_factory = sqlite3.Row
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    id_ultima_medicao_origem,
                    data_hora_ultima_medicao,
                    nivel_alerta,
                    mensagem_alerta,
                    justificativa_alerta,
                    gerado_em
                FROM alertas_chuva
                ORDER BY id_ultima_medicao_origem ASC
                LIMIT ?
                """,
                (limite,),
            )

            linhas = cursor.fetchall()

        return [dict(linha) for linha in linhas]

    def remover_todos_alertas(self) -> int:
        """Remove todos os alertas persistidos."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM alertas_chuva")
            conexao.commit()
            return int(cursor.rowcount)

    def _agora_iso(self) -> str:
        """Gera timestamp em formato ISO para o instante do alerta."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")