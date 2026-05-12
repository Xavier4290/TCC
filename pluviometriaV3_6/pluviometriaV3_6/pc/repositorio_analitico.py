import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from pc.analisador_evento import ResultadoAnaliseEvento
from app.modelos import Medicao


class RepositorioAnaliticoSQLite:
    """
    Repositório da camada analítica no banco central do PC.

    Guarda o resultado das análises em tabela separada da tabela de medições
    brutas, preservando rastreabilidade e permitindo recalcular a análise no futuro.
    """

    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao

    def inicializar_banco(self) -> None:
        """Cria a tabela de análises."""
        cursor = self.conexao.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analises_chuva (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_ultima_medicao_origem INTEGER NOT NULL UNIQUE,
                    data_hora_ultima_medicao TIMESTAMP NOT NULL,
                    quantidade_medicoes INTEGER NOT NULL,
                    intervalo_medicao_segundos INTEGER NOT NULL,
                    janela_total_segundos INTEGER NOT NULL,
                    pulsos_totais INTEGER NOT NULL,
                    chuva_total_mm REAL NOT NULL,
                    taxa_equivalente_mm_h REAL NOT NULL,
                    media_pulsos_por_intervalo REAL NOT NULL,
                    media_mm_por_intervalo REAL NOT NULL,
                    max_pulsos_em_intervalo INTEGER NOT NULL,
                    max_mm_em_intervalo REAL NOT NULL,
                    intervalos_com_chuva INTEGER NOT NULL,
                    percentual_intervalos_com_chuva REAL NOT NULL,
                    consecutivos_finais_com_chuva INTEGER NOT NULL,
                    tendencia_taxa_mm_h REAL NOT NULL,
                    direcao_tendencia VARCHAR(50) NOT NULL,
                    indice_atividade_imediata REAL NOT NULL,
                    classificacao_chuva VARCHAR(50) NOT NULL,
                    severidade_operacional VARCHAR(50) NOT NULL,
                    tendencia_final VARCHAR(50) NOT NULL,
                    sinal_pre_alerta VARCHAR(50) NOT NULL,
                    alerta_recomendado VARCHAR(50) NOT NULL,
                    score_confianca REAL NOT NULL,
                    justificativa_resumida TEXT NOT NULL,
                    analisado_em TIMESTAMP NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analises_chuva_id_ultima
                ON analises_chuva (id_ultima_medicao_origem)
            """)

            self.conexao.commit()
        finally:
            cursor.close()

    def inserir_ou_confirmar_analise(
        self,
        id_ultima_medicao_origem: int,
        data_hora_ultima_medicao: str,
        resultado: ResultadoAnaliseEvento,
    ) -> bool:

        if id_ultima_medicao_origem <= 0:
            raise ValueError("id_ultima_medicao_origem deve ser maior que zero.")

        analisado_em = self._agora()
        features = resultado.features
        classificacao = resultado.classificacao

        cursor = self.conexao.cursor()
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO analises_chuva (
                    id_ultima_medicao_origem,
                    data_hora_ultima_medicao,
                    quantidade_medicoes,
                    intervalo_medicao_segundos,
                    janela_total_segundos,
                    pulsos_totais,
                    chuva_total_mm,
                    taxa_equivalente_mm_h,
                    media_pulsos_por_intervalo,
                    media_mm_por_intervalo,
                    max_pulsos_em_intervalo,
                    max_mm_em_intervalo,
                    intervalos_com_chuva,
                    percentual_intervalos_com_chuva,
                    consecutivos_finais_com_chuva,
                    tendencia_taxa_mm_h,
                    direcao_tendencia,
                    indice_atividade_imediata,
                    classificacao_chuva,
                    severidade_operacional,
                    tendencia_final,
                    sinal_pre_alerta,
                    alerta_recomendado,
                    score_confianca,
                    justificativa_resumida,
                    analisado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id_ultima_medicao_origem,
                    data_hora_ultima_medicao,
                    features.quantidade_medicoes,
                    features.intervalo_medicao_segundos,
                    features.janela_total_segundos,
                    features.pulsos_totais,
                    features.chuva_total_mm,
                    features.taxa_equivalente_mm_h,
                    features.media_pulsos_por_intervalo,
                    features.media_mm_por_intervalo,
                    features.max_pulsos_em_intervalo,
                    features.max_mm_em_intervalo,
                    features.intervalos_com_chuva,
                    features.percentual_intervalos_com_chuva,
                    features.consecutivos_finais_com_chuva,
                    features.tendencia_taxa_mm_h,
                    features.direcao_tendencia,
                    features.indice_atividade_imediata,
                    classificacao.classificacao_chuva,
                    classificacao.severidade_operacional,
                    classificacao.tendencia_final,
                    classificacao.sinal_pre_alerta,
                    classificacao.alerta_recomendado,
                    classificacao.score_confianca,
                    classificacao.justificativa_resumida,
                    analisado_em,
                ),
            )

            self.conexao.commit()
            return True
        except Exception as e:
            print(f"Erro ao inserir análise: {e}")
            return False
        finally:
            cursor.close()

    def analise_existe(self, id_ultima_medicao_origem: int) -> bool:
        """Verifica se já existe análise persistida para a medição informada."""
        cursor = self.conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT 1
                FROM analises_chuva
                WHERE id_ultima_medicao_origem = ?
                LIMIT 1
                """,
                (id_ultima_medicao_origem,),
            )

            linha = cursor.fetchone()
            return linha is not None
        finally:
            cursor.close()

    def contar_analises(self) -> int:
        """Retorna a quantidade total de análises persistidas."""
        cursor = self.conexao.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM analises_chuva")
            resultado = cursor.fetchone()
            return int(resultado[0]) if resultado else 0
        finally:
            cursor.close()

    def listar_todas(self, limite: int = 100) -> List[Dict[str, object]]:
        """Lista as análises persistidas, ordenadas pela medição final de origem."""
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        cursor = self.conexao.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    id,
                    id_ultima_medicao_origem,
                    data_hora_ultima_medicao,
                    quantidade_medicoes,
                    janela_total_segundos,
                    chuva_total_mm,
                    taxa_equivalente_mm_h,
                    percentual_intervalos_com_chuva,
                    consecutivos_finais_com_chuva,
                    direcao_tendencia,
                    indice_atividade_imediata,
                    classificacao_chuva,
                    severidade_operacional,
                    tendencia_final,
                    sinal_pre_alerta,
                    alerta_recomendado,
                    score_confianca,
                    justificativa_resumida,
                    analisado_em
                FROM analises_chuva
                ORDER BY id_ultima_medicao_origem ASC
                LIMIT ?
                """,
                (limite,),
            )

            colunas = [desc[0] for desc in cursor.description]
            linhas = cursor.fetchall()

            return [dict(zip(colunas, linha)) for linha in linhas]
        finally:
            cursor.close()

    def remover_todas_analises(self) -> int:
        """Remove todas as análises persistidas."""
        cursor = self.conexao.cursor()
        try:
            cursor.execute("DELETE FROM analises_chuva")
            linhas_afetadas = cursor.rowcount
            self.conexao.commit()
            return linhas_afetadas if linhas_afetadas is not None else 0
        finally:
            cursor.close()

    def _agora(self) -> str:
        """Retorna timestamp atual como string ISO format (compatível com SQLite)."""
        return datetime.now().isoformat()