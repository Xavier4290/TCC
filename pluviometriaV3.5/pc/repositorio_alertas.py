import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import psycopg2

from app.config import CONFIG_POSTGRES
from pc.gerador_alertas import ResultadoGeracaoAlerta
from psycopg2.extensions import connection


class RepositorioAlertasSQLite:
    """
    Repositório da camada de alertas no banco central do PC.

    Mantém os alertas em tabela separada da análise, preservando a evolução
    arquitetural do projeto e permitindo inspeção operacional independente.
    """
    
    def __init__(self, conexao: connection) -> None:
        self.conexao = conexao

    @staticmethod
    def criar_conexao() -> connection:
        """Cria e retorna uma nova conexão com o PostgreSQL."""
        return psycopg2.connect(**CONFIG_POSTGRES)

    def inicializar_banco(self) -> None:
        """Cria a tabela de alertas e índices necessários."""

        with self.conexao.cursor() as cursor:
            self._criar_tabela(cursor)
            self._criar_indices(cursor)

        self.conexao.commit()

    def _criar_tabela(self, cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alertas_chuva (
                id SERIAL PRIMARY KEY,
                id_ultima_medicao_origem INTEGER NOT NULL UNIQUE,
                data_hora_ultima_medicao TIMESTAMP NOT NULL,
                nivel_alerta TEXT NOT NULL,
                mensagem_alerta TEXT NOT NULL,
                justificativa_alerta TEXT NOT NULL,
                gerado_em TIMESTAMP NOT NULL
            )
            """
        )

    def _criar_indices(self, cursor) -> None:
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alertas_chuva_id_ultima
            ON alertas_chuva (id_ultima_medicao_origem)
            """
        )

    def inserir_ou_confirmar_alerta(
        self,
        id_ultima_medicao_origem: int,
        data_hora_ultima_medicao,
        resultado_alerta: ResultadoGeracaoAlerta,
    ) -> bool:
        """
        Insere o alerta ou ignora caso já exista.
        """

        if id_ultima_medicao_origem <= 0:
            raise ValueError("id_ultima_medicao_origem deve ser maior que zero.")

        gerado_em = self._agora()

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO alertas_chuva (
                    id_ultima_medicao_origem,
                    data_hora_ultima_medicao,
                    nivel_alerta,
                    mensagem_alerta,
                    justificativa_alerta,
                    gerado_em
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_ultima_medicao_origem) DO NOTHING
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

            inseriu = cursor.rowcount == 1

        self.conexao.commit()

        return inseriu or self.alerta_existe(id_ultima_medicao_origem)

    def alerta_existe(self, id_ultima_medicao_origem: int) -> bool:
        """Verifica se já existe alerta para a medição informada."""

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM alertas_chuva
                WHERE id_ultima_medicao_origem = %s
                LIMIT 1
                """,
                (id_ultima_medicao_origem,),
            )

            linha = cursor.fetchone()

        return linha is not None

    def contar_alertas(self) -> int:
        """Retorna a quantidade total de alertas persistidos."""

        with self.conexao.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM alertas_chuva")
            resultado = cursor.fetchone()

        return int(resultado[0]) if resultado else 0

    def listar_todos(self, limite: int = 100) -> List[Dict[str, object]]:
        """Lista os alertas persistidos."""

        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        with self.conexao.cursor() as cursor:
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
                LIMIT %s
                """,
                (limite,),
            )

            colunas = [desc[0] for desc in cursor.description]
            linhas = cursor.fetchall()

        return [dict(zip(colunas, linha)) for linha in linhas]

    def remover_todos_alertas(self) -> int:
        """Remove todos os alertas persistidos."""

        with self.conexao.cursor() as cursor:
            cursor.execute("DELETE FROM alertas_chuva")
            linhas_removidas = cursor.rowcount

        self.conexao.commit()

        return int(linhas_removidas)

    def _agora(self) -> datetime:
        """Retorna o timestamp atual como datetime."""
        return datetime.now()