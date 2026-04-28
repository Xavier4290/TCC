import psycopg2

from psycopg2.extensions import connection
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from app.config import CONFIG_POSTGRES


import sys


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import CONFIG_POSTGRES 
from app.modelos import Medicao

class RepositorioCentralSQLite:
    """
    Repositório da base central do lado do PC.
    Nesta fase, ele persiste os lotes recebidos em SQLite para validar durabilidade.
    """

    def __init__(self, conexao):
        self.conexao = conexao
        
    @staticmethod
    def criar_conexao() -> connection:
        """Cria e retorna uma nova conexão com o PostgreSQL."""
        return psycopg2.connect(**CONFIG_POSTGRES)  

    def inicializar_banco(self) -> None:
        """Cria a tabela central de medições recebidas, caso ainda não exista."""

        with self.conexao.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medicoes_recebidas (
                    id SERIAL PRIMARY KEY,
                    id_origem INTEGER NOT NULL UNIQUE,
                    data_hora TIMESTAMP NOT NULL,
                    pulsos INTEGER NOT NULL CHECK (pulsos >= 0),
                    chuva_intervalo_mm DOUBLE PRECISION NOT NULL CHECK (chuva_intervalo_mm >= 0),
                    chuva_acumulada_mm DOUBLE PRECISION NOT NULL CHECK (chuva_acumulada_mm >= 0),
                    recebido_em TIMESTAMP NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_medicoes_recebidas_id_origem
                ON medicoes_recebidas (id_origem)
            """)

        self.conexao.commit()

    def inserir_ou_confirmar_medicao(self, medicao: dict) -> bool:
        """
        Insere a medição centralmente ou ignora caso já exista.
        Operação idempotente via constraint UNIQUE.
        """

        id_origem = int(medicao["id"])
        recebido_em = self._agora()

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO medicoes_recebidas (
                    id_origem,
                    data_hora,
                    pulsos,
                    chuva_intervalo_mm,
                    chuva_acumulada_mm,
                    recebido_em
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_origem)
                DO NOTHING
                """,
                (
                    id_origem,
                    medicao["data_hora"],
                    medicao["pulsos"],
                    medicao["chuva_intervalo_mm"],
                    medicao["chuva_acumulada_mm"],
                    recebido_em,
                ),
            )

            resultado = cursor.fetchone()
            self.conexao.commit()

            return resultado is not None

    def registro_existe(self, id_origem: int) -> bool:
        """Verifica se a medição de origem já existe na base central."""

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM medicoes_recebidas
                WHERE id_origem = %s
                LIMIT 1
                """,
                (id_origem,),
            )

            linha = cursor.fetchone()

        return linha is not None

    def contar_registros(self) -> int:
        """Retorna a quantidade total de medições recebidas na base central."""

        with self.conexao.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM medicoes_recebidas"
            )
            resultado = cursor.fetchone()

        return int(resultado[0]) if resultado else 0

    def listar_todas(self, limite: int = 100) -> List[Dict[str, object]]:
        """Lista os registros da base central, ordenados por ID de origem."""

        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    id_origem,
                    data_hora,
                    pulsos,
                    chuva_intervalo_mm,
                    chuva_acumulada_mm,
                    recebido_em
                FROM medicoes_recebidas
                ORDER BY id_origem ASC
                LIMIT %s
                """,
                (limite,),
            )

            colunas = [desc[0] for desc in cursor.description]
            linhas = cursor.fetchall()

            return [dict(zip(colunas, linha)) for linha in linhas]

    def remover_todos_registros(self) -> int:
        """Remove todos os registros da base central de desenvolvimento."""

        with self.conexao.cursor() as cursor:
            cursor.execute("DELETE FROM medicoes_recebidas")

            self.conexao.commit()

            return cursor.rowcount

    def _agora(self) -> datetime:
        """Retorna timestamp atual como datetime (compatível com PostgreSQL)."""
        return datetime.now()
    
    def listar_ultimas_medicoes_como_modelos(self, limite: int = 6) -> list[Medicao]:
        """
        Retorna as últimas medições centrais em ordem cronológica crescente,
        convertidas para o modelo Medicao.
        """

        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id_origem,
                    data_hora,
                    pulsos,
                    chuva_intervalo_mm,
                    chuva_acumulada_mm
                FROM medicoes_recebidas
                ORDER BY id_origem DESC
                LIMIT %s
                """,
                (limite,),
            )

            linhas = cursor.fetchall()

        linhas_ordenadas = list(reversed(linhas))

        return [
            Medicao(
                data_hora=str(linha[1]),
                pulsos=int(linha[2]),
                chuva_intervalo_mm=float(linha[3]),
                chuva_acumulada_mm=float(linha[4]),
            )
            for linha in linhas_ordenadas
        ]

    def listar_ultimas_medicoes_brutas(self, limite: int = 6) -> list[dict]:
            """
            Retorna as últimas medições centrais em ordem cronológica crescente,
            preservando o id_origem.
            """

            if limite <= 0:
                raise ValueError("O limite deve ser maior que zero.")

            with self.conexao.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id_origem,
                        data_hora,
                        pulsos,
                        chuva_intervalo_mm,
                        chuva_acumulada_mm
                    FROM medicoes_recebidas
                    ORDER BY id_origem DESC
                    LIMIT %s
                    """,
                    (limite,),
                )

                colunas = [desc[0] for desc in cursor.description]
                linhas = cursor.fetchall()

            return [
                dict(zip(colunas, linha))
                for linha in reversed(linhas)
            ]


    def listar_ultimas_medicoes_como_modelos(self, limite: int = 6) -> list[Medicao]:
        """
        Retorna as últimas medições centrais em ordem cronológica crescente,
        convertidas para o modelo Medicao.
        """

        registros = self.listar_ultimas_medicoes_brutas(limite=limite)

        return [
            Medicao(
                data_hora=str(registro["data_hora"]),
                pulsos=int(registro["pulsos"]),
                chuva_intervalo_mm=float(registro["chuva_intervalo_mm"]),
                chuva_acumulada_mm=float(registro["chuva_acumulada_mm"]),
            )
            for registro in registros
        ]