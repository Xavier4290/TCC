import sqlite3
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


from app.config import CONFIG_POSTGRES
from pc.gerador_alertas import ResultadoGeracaoAlerta
from psycopg2.extensions import connection


ORDEM_NIVEL_ALERTA = {
    "sem_alerta": 0,
    "pre_alerta": 1,
    "atencao": 2,
    "alerta_moderado": 3,
    "alerta_alto": 4,
}


class RepositorioAlertasCicloSQLite:
    """
    Repositório de alertas com ciclo de vida.

    Em vez de criar um alerta novo a cada análise relevante, esta camada
    permite abrir, atualizar e encerrar o mesmo alerta conforme o evento evolui.
    """

    # def __init__(self, caminho_banco: Path | str = CAMINHO_BANCO_CENTRAL_PC) -> None:
    #     self.caminho_banco = Path(caminho_banco)
    #     self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)
        
    def __init__(self, conexao: connection) -> None:
        self.conexao = conexao
        
    def _criar_conexao(self) -> connection:
        """Cria conexão com o PostgreSQL"""
        try:
            return psycopg2.connect(
                host=CONFIG_POSTGRES["host"],
                user=CONFIG_POSTGRES["user"],
                password=CONFIG_POSTGRES["password"],
                database=CONFIG_POSTGRES["database"]
            )
        except Exception as e:
            raise RuntimeError(f"Erro ao conectar no banco: {e}")


    def inicializar_banco(self) -> None:
        """Cria a tabela de alertas com ciclo de vida, caso ainda não exista."""

        with self.conexao.cursor() as cursor:

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alertas_evento (
                    id SERIAL PRIMARY KEY,
                    status_alerta TEXT NOT NULL,
                    nivel_alerta_atual TEXT NOT NULL,
                    nivel_alerta_maximo TEXT NOT NULL,
                    primeira_medicao_origem INTEGER NOT NULL,
                    ultima_medicao_origem INTEGER NOT NULL,
                    data_hora_primeira_medicao TIMESTAMP NOT NULL,
                    data_hora_ultima_medicao TIMESTAMP NOT NULL,
                    mensagem_alerta TEXT NOT NULL,
                    justificativa_alerta TEXT NOT NULL,
                    mensagem_encerramento TEXT,
                    justificativa_encerramento TEXT,
                    aberto_em TIMESTAMP NOT NULL,
                    atualizado_em TIMESTAMP,
                    encerrado_em TIMESTAMP,
                    quantidade_atualizacoes INTEGER NOT NULL DEFAULT 0
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alertas_evento_status
                ON alertas_evento (status_alerta)
                """
            )

        self.conexao.commit()

    def buscar_alerta_ativo(self) -> Optional[Dict[str, object]]:
        """Busca o alerta atualmente aberto ou atualizado, se existir."""

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM alertas_evento
                WHERE status_alerta IN (%s, %s)
                ORDER BY id DESC
                LIMIT 1
                """,
                ("ABERTO", "ATUALIZADO"),
            )

            linha = cursor.fetchone()

            if linha is None:
                return None

            colunas = [desc[0] for desc in cursor.description]
            return dict(zip(colunas, linha))

    def abrir_alerta(
        self,
        id_ultima_medicao_origem: int,
        data_hora_ultima_medicao: str,
        resultado_alerta: ResultadoGeracaoAlerta,
    ) -> int:
        """Abre um novo alerta de evento."""

        aberto_em = self._agora_iso()

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO alertas_evento (
                    status_alerta,
                    nivel_alerta_atual,
                    nivel_alerta_maximo,
                    primeira_medicao_origem,
                    ultima_medicao_origem,
                    data_hora_primeira_medicao,
                    data_hora_ultima_medicao,
                    mensagem_alerta,
                    justificativa_alerta,
                    aberto_em,
                    quantidade_atualizacoes
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    "ABERTO",
                    resultado_alerta.nivel_alerta,
                    resultado_alerta.nivel_alerta,
                    id_ultima_medicao_origem,
                    id_ultima_medicao_origem,
                    data_hora_ultima_medicao,
                    data_hora_ultima_medicao,
                    resultado_alerta.mensagem_alerta,
                    resultado_alerta.justificativa_alerta,
                    aberto_em,
                    0,
                ),
            )

            novo_id = cursor.fetchone()[0]

        self.conexao.commit()

        return novo_id

    def atualizar_alerta(
        self,
        alerta_id: int,
        id_ultima_medicao_origem: int,
        data_hora_ultima_medicao: str,
        resultado_alerta: ResultadoGeracaoAlerta,
    ) -> int:
        """Atualiza o alerta ativo com o novo estado do evento."""

        atualizado_em = self._agora_iso()

        alerta_atual = self._buscar_alerta_por_id(alerta_id)
        if alerta_atual is None:
            raise ValueError(f"Alerta {alerta_id} não encontrado.")

        nivel_maximo = self._calcular_nivel_maximo(
            str(alerta_atual["nivel_alerta_maximo"]),
            resultado_alerta.nivel_alerta,
        )

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                UPDATE alertas_evento
                SET
                    status_alerta = %s,
                    nivel_alerta_atual = %s,
                    nivel_alerta_maximo = %s,
                    ultima_medicao_origem = %s,
                    data_hora_ultima_medicao = %s,
                    mensagem_alerta = %s,
                    justificativa_alerta = %s,
                    atualizado_em = %s,
                    quantidade_atualizacoes = quantidade_atualizacoes + 1
                WHERE id = %s
                """,
                (
                    "ATUALIZADO",
                    resultado_alerta.nivel_alerta,
                    nivel_maximo,
                    id_ultima_medicao_origem,
                    data_hora_ultima_medicao,
                    resultado_alerta.mensagem_alerta,
                    resultado_alerta.justificativa_alerta,
                    atualizado_em,
                    alerta_id,
                ),
            )

            self.conexao.commit()

            return cursor.rowcount

    def encerrar_alerta(
        self,
        alerta_id: int,
        mensagem_encerramento: str,
        justificativa_encerramento: str,
    ) -> int:
        """Encerra um alerta ativo."""

        encerrado_em = self._agora_iso()

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                UPDATE alertas_evento
                SET
                    status_alerta = %s,
                    mensagem_encerramento = %s,
                    justificativa_encerramento = %s,
                    encerrado_em = %s
                WHERE id = %s
                AND status_alerta IN (%s, %s)
                """,
                (
                    "ENCERRADO",
                    mensagem_encerramento,
                    justificativa_encerramento,
                    encerrado_em,
                    alerta_id,
                    "ABERTO",
                    "ATUALIZADO",
                ),
            )

            self.conexao.commit()

            return cursor.rowcount

    def contar_alertas(self) -> int:
        """Retorna a quantidade total de alertas persistidos."""

        with self.conexao.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM alertas_evento")
            resultado = cursor.fetchone()

        return int(resultado[0]) if resultado else 0

    def listar_todos(self, limite: int = 100) -> List[Dict[str, object]]:
        """Lista todos os alertas com ciclo de vida."""

        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    status_alerta,
                    nivel_alerta_atual,
                    nivel_alerta_maximo,
                    primeira_medicao_origem,
                    ultima_medicao_origem,
                    data_hora_primeira_medicao,
                    data_hora_ultima_medicao,
                    quantidade_atualizacoes,
                    aberto_em,
                    atualizado_em,
                    encerrado_em
                FROM alertas_evento
                ORDER BY id ASC
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
            cursor.execute("DELETE FROM alertas_evento")

            self.conexao.commit()

            return cursor.rowcount

    def _buscar_alerta_por_id(self, alerta_id: int) -> Optional[Dict[str, object]]:
        """Busca um alerta específico pelo ID."""

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM alertas_evento
                WHERE id = %s
                LIMIT 1
                """,
                (alerta_id,),
            )

            linha = cursor.fetchone()

            if linha is None:
                return None

            colunas = [desc[0] for desc in cursor.description]
            return dict(zip(colunas, linha))

    def _calcular_nivel_maximo(self, nivel_atual: str, nivel_novo: str) -> str:
        """Mantém o maior nível de alerta já atingido no evento."""

        if ORDEM_NIVEL_ALERTA.get(nivel_novo, 0) >= ORDEM_NIVEL_ALERTA.get(nivel_atual, 0):
            return nivel_novo

        return nivel_atual

    def _agora_iso(self) -> str:
        """Gera timestamp em formato ISO para o instante atual."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")