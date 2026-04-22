import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from app.config import CAMINHO_BANCO_CENTRAL_PC
from pc.analisador_evento import ResultadoAnaliseEvento
from app.modelos import Medicao


class RepositorioAnaliticoSQLite:
    """
    Repositório da camada analítica no banco central do PC.

    Guarda o resultado das análises em tabela separada da tabela de medições
    brutas, preservando rastreabilidade e permitindo recalcular a análise no futuro.
    """

    def __init__(self, caminho_banco: Path | str = CAMINHO_BANCO_CENTRAL_PC) -> None:
        self.caminho_banco = Path(caminho_banco)
        self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)

    def inicializar_banco(self) -> None:
        """Cria a tabela de análises, caso ainda não exista."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS analises_chuva (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_ultima_medicao_origem INTEGER NOT NULL UNIQUE,
                    data_hora_ultima_medicao TEXT NOT NULL,
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
                    direcao_tendencia TEXT NOT NULL,
                    indice_atividade_imediata REAL NOT NULL,
                    classificacao_chuva TEXT NOT NULL,
                    severidade_operacional TEXT NOT NULL,
                    tendencia_final TEXT NOT NULL,
                    sinal_pre_alerta TEXT NOT NULL,
                    alerta_recomendado TEXT NOT NULL,
                    score_confianca REAL NOT NULL,
                    justificativa_resumida TEXT NOT NULL,
                    analisado_em TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_analises_chuva_id_ultima
                ON analises_chuva (id_ultima_medicao_origem)
                """
            )

            conexao.commit()

    def inserir_ou_confirmar_analise(
        self,
        id_ultima_medicao_origem: int,
        data_hora_ultima_medicao: str,
        resultado: ResultadoAnaliseEvento,
    ) -> bool:
        """
        Insere a análise da janela ou confirma como válida caso ela já exista.
        Isso torna a persistência analítica idempotente para a mesma medição final.
        """
        if id_ultima_medicao_origem <= 0:
            raise ValueError("id_ultima_medicao_origem deve ser maior que zero.")

        analisado_em = self._agora_iso()
        features = resultado.features
        classificacao = resultado.classificacao

        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

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

            conexao.commit()

            if cursor.rowcount == 1:
                return True

        return self.analise_existe(id_ultima_medicao_origem)

    def analise_existe(self, id_ultima_medicao_origem: int) -> bool:
        """Verifica se já existe análise persistida para a medição final informada."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
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

    def contar_analises(self) -> int:
        """Retorna a quantidade total de análises persistidas."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT COUNT(*) FROM analises_chuva")
            resultado = cursor.fetchone()

        return int(resultado[0])

    def listar_todas(self, limite: int = 100) -> List[Dict[str, object]]:
        """Lista as análises persistidas, ordenadas pela medição final de origem."""
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

            linhas = cursor.fetchall()

        return [dict(linha) for linha in linhas]

    def remover_todas_analises(self) -> int:
        """Remove todas as análises persistidas."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM analises_chuva")
            conexao.commit()
            return int(cursor.rowcount)

    def _agora_iso(self) -> str:
        """Gera timestamp em formato ISO para o instante da análise."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    