import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from app.config import CAMINHO_BANCO_CENTRAL_PC
from app.modelos import Medicao


class RepositorioCentralSQLite:
    """
    Repositório da base central do lado do PC.
    Nesta fase, ele persiste os lotes recebidos em SQLite para validar durabilidade.
    """

    def __init__(self, caminho_banco: Path | str = CAMINHO_BANCO_CENTRAL_PC) -> None:
        self.caminho_banco = Path(caminho_banco)
        self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)

    def inicializar_banco(self) -> None:
        """Cria a tabela central de medições recebidas, caso ainda não exista."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS medicoes_recebidas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_origem INTEGER NOT NULL UNIQUE,
                    data_hora TEXT NOT NULL,
                    pulsos INTEGER NOT NULL CHECK (pulsos >= 0),
                    chuva_intervalo_mm REAL NOT NULL CHECK (chuva_intervalo_mm >= 0),
                    chuva_acumulada_mm REAL NOT NULL CHECK (chuva_acumulada_mm >= 0),
                    recebido_em TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_medicoes_recebidas_id_origem
                ON medicoes_recebidas (id_origem)
                """
            )

            conexao.commit()

    def inserir_ou_confirmar_medicao(self, medicao: dict) -> bool:
        """
        Insere a medição centralmente ou confirma como válida caso ela já exista.
        Esse comportamento torna o recebimento idempotente para reenvios futuros.
        """
        id_origem = int(medicao["id"])
        recebido_em = self._agora_iso()

        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

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

            conexao.commit()

            if cursor.rowcount == 1:
                return True

        return self.registro_existe(id_origem)

    def registro_existe(self, id_origem: int) -> bool:
        """Verifica se a medição de origem já existe na base central."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
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

    def contar_registros(self) -> int:
        """Retorna a quantidade total de medições recebidas na base central."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT COUNT(*) FROM medicoes_recebidas")
            resultado = cursor.fetchone()

        return int(resultado[0])

    def listar_todas(self, limite: int = 100) -> List[Dict[str, object]]:
        """Lista os registros da base central, ordenados por ID de origem."""
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        with sqlite3.connect(self.caminho_banco) as conexao:
            conexao.row_factory = sqlite3.Row
            cursor = conexao.cursor()

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

            linhas = cursor.fetchall()

        return [dict(linha) for linha in linhas]

    def remover_todos_registros(self) -> int:
        """Remove todos os registros da base central de desenvolvimento."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM medicoes_recebidas")
            conexao.commit()
            return int(cursor.rowcount)

    def _agora_iso(self) -> str:
        """Gera timestamp em formato ISO para o instante de recebimento central."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def listar_ultimas_medicoes_como_modelos(self, limite: int = 6) -> list[Medicao]:
        """
        Retorna as últimas medições centrais em ordem cronológica crescente,
        convertidas para o modelo Medicao.
        """
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        with sqlite3.connect(self.caminho_banco) as conexao:
            conexao.row_factory = sqlite3.Row
            cursor = conexao.cursor()

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

            linhas = cursor.fetchall()

        linhas_ordenadas = list(reversed(linhas))

        return [
            Medicao(
                data_hora=str(linha["data_hora"]),
                pulsos=int(linha["pulsos"]),
                chuva_intervalo_mm=float(linha["chuva_intervalo_mm"]),
                chuva_acumulada_mm=float(linha["chuva_acumulada_mm"]),
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

        with sqlite3.connect(self.caminho_banco) as conexao:
            conexao.row_factory = sqlite3.Row
            cursor = conexao.cursor()

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

            linhas = cursor.fetchall()

        return [dict(linha) for linha in reversed(linhas)]


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