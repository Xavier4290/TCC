import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modelos import Medicao


class RepositorioCentralSQLite:
    """
    Repositório da base central do lado do PC.
    Persiste os lotes recebidos em SQLite para validar durabilidade.
    """

    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao

    def inicializar_banco(self) -> None:
        """Cria a tabela central de medições recebidas, caso ainda não exista."""
        cursor = self.conexao.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medicoes_recebidas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_origem INTEGER NOT NULL UNIQUE,
                    data_hora TIMESTAMP NOT NULL,
                    pulsos INTEGER NOT NULL CHECK (pulsos >= 0),
                    chuva_intervalo_mm REAL NOT NULL CHECK (chuva_intervalo_mm >= 0),
                    chuva_acumulada_mm REAL NOT NULL CHECK (chuva_acumulada_mm >= 0),
                    recebido_em TIMESTAMP NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_medicoes_recebidas_id_origem
                ON medicoes_recebidas (id_origem)
            """)
            
            self.conexao.commit()
        finally:
            cursor.close()

    def inserir_ou_confirmar_medicao(self, medicao: dict) -> bool:
        """
        Insere a medição centralmente ou ignora caso já exista.
        Operação idempotente via constraint UNIQUE.
        """
        id_origem = int(medicao["id"])
        recebido_em = self._agora()

        cursor = self.conexao.cursor()
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO medicoes_recebidas (
                    id_origem,
                    data_hora,
                    pulsos,
                    chuva_intervalo_mm,
                    chuva_acumulada_mm,
                    recebido_em
                )
                VALUES (?, ?, ?, ?, ?, ?)
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

            self.conexao.commit()
            return True
        except Exception as e:
            print(f"Erro ao inserir medição: {e}")
            return False
        finally:
            cursor.close()

    def registro_existe(self, id_origem: int) -> bool:
        """Verifica se a medição de origem já existe na base central."""
        cursor = self.conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT 1
                FROM medicoes_recebidas
                WHERE id_origem = ?
                LIMIT 1
                """,
                (id_origem,),
            )

            linha = cursor.fetchone()
            return linha is not None
        finally:
            cursor.close()

    def contar_registros(self) -> int:
        """Retorna a quantidade total de medições recebidas na base central."""
        cursor = self.conexao.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM medicoes_recebidas")
            resultado = cursor.fetchone()
            return int(resultado[0]) if resultado else 0
        finally:
            cursor.close()

    def listar_todas(self, limite: int = 100) -> List[Dict[str, object]]:
        """Lista os registros da base central, ordenados por ID de origem."""
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        cursor = self.conexao.cursor()
        try:
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
                LIMIT ?
                """,
                (limite,),
            )

            colunas = [desc[0] for desc in cursor.description]
            linhas = cursor.fetchall()

            return [dict(zip(colunas, linha)) for linha in linhas]
        finally:
            cursor.close()

    def remover_todos_registros(self) -> int:
        """Remove todos os registros da base central de desenvolvimento."""
        cursor = self.conexao.cursor()
        try:
            cursor.execute("DELETE FROM medicoes_recebidas")
            self.conexao.commit()
            return cursor.rowcount
        finally:
            cursor.close()

    def _agora(self) -> str:
        """Retorna timestamp atual como string ISO format (compatível com SQLite)."""
        return datetime.now().isoformat()

    def listar_ultimas_medicoes_brutas(self, limite: int = 6) -> list[dict]:
        """
        Retorna as últimas medições centrais em ordem cronológica crescente,
        preservando o id_origem.
        """
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        cursor = self.conexao.cursor()
        try:
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
                LIMIT ?
                """,
                (limite,),
            )

            colunas = [desc[0] for desc in cursor.description]
            linhas = cursor.fetchall()

            return [
                dict(zip(colunas, linha))
                for linha in reversed(linhas)
            ]
        finally:
            cursor.close()

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