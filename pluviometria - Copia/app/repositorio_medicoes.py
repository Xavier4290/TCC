import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import CAMINHO_BANCO_SQLITE, STATUS_ENVIADO, STATUS_PENDENTE
from .modelos import Medicao, MedicaoPersistida


class RepositorioMedicoesSQLite:
    """Centraliza o acesso ao banco SQLite local de medições."""

    def __init__(self, caminho_banco: Path | str = CAMINHO_BANCO_SQLITE) -> None:
        self.caminho_banco = Path(caminho_banco)
        self._garantir_diretorio_banco()

    def inicializar_banco(self) -> None:
        """Cria a tabela principal e os índices necessários, caso não existam."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS medicoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_hora TEXT NOT NULL,
                    pulsos INTEGER NOT NULL CHECK (pulsos >= 0),
                    chuva_intervalo_mm REAL NOT NULL CHECK (chuva_intervalo_mm >= 0),
                    chuva_acumulada_mm REAL NOT NULL CHECK (chuva_acumulada_mm >= 0),
                    status_sync TEXT NOT NULL DEFAULT 'PENDENTE'
                        CHECK (status_sync IN ('PENDENTE', 'ENVIADO')),
                    tentativas_envio INTEGER NOT NULL DEFAULT 0
                        CHECK (tentativas_envio >= 0),
                    criado_em TEXT NOT NULL,
                    enviado_em TEXT,
                    ultimo_erro TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_medicoes_status_id
                ON medicoes (status_sync, id)
                """
            )

            conexao.commit()

    def inserir_medicao(self, medicao: Medicao) -> int:
        """Insere uma nova medição no banco com status inicial PENDENTE."""
        self._validar_medicao(medicao)
        criado_em = self._agora_iso()

        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT INTO medicoes (
                    data_hora,
                    pulsos,
                    chuva_intervalo_mm,
                    chuva_acumulada_mm,
                    status_sync,
                    tentativas_envio,
                    criado_em,
                    enviado_em,
                    ultimo_erro
                )
                VALUES (?, ?, ?, ?, ?, 0, ?, NULL, NULL)
                """,
                (
                    medicao.data_hora,
                    medicao.pulsos,
                    medicao.chuva_intervalo_mm,
                    medicao.chuva_acumulada_mm,
                    STATUS_PENDENTE,
                    criado_em,
                ),
            )

            conexao.commit()
            return int(cursor.lastrowid)

    def buscar_pendentes(self, limite: int = 10) -> List[MedicaoPersistida]:
        """Retorna os registros pendentes mais antigos, respeitando o limite informado."""
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        with sqlite3.connect(self.caminho_banco) as conexao:
            conexao.row_factory = sqlite3.Row
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    data_hora,
                    pulsos,
                    chuva_intervalo_mm,
                    chuva_acumulada_mm,
                    status_sync,
                    tentativas_envio,
                    criado_em,
                    enviado_em,
                    ultimo_erro
                FROM medicoes
                WHERE status_sync = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (STATUS_PENDENTE, limite),
            )

            linhas = cursor.fetchall()

        return [self._linha_para_medicao_persistida(linha) for linha in linhas]

    def contar_pendentes(self) -> int:
        """Retorna a quantidade total de registros ainda pendentes de sincronização."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM medicoes
                WHERE status_sync = ?
                """,
                (STATUS_PENDENTE,),
            )
            resultado = cursor.fetchone()

        return int(resultado[0])

    def buscar_pendente_mais_antigo(self) -> Optional[MedicaoPersistida]:
        """Retorna o registro pendente mais antigo, ou None quando não houver pendências."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            conexao.row_factory = sqlite3.Row
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    data_hora,
                    pulsos,
                    chuva_intervalo_mm,
                    chuva_acumulada_mm,
                    status_sync,
                    tentativas_envio,
                    criado_em,
                    enviado_em,
                    ultimo_erro
                FROM medicoes
                WHERE status_sync = ?
                ORDER BY criado_em ASC, id ASC
                LIMIT 1
                """,
                (STATUS_PENDENTE,),
            )

            linha = cursor.fetchone()

        if linha is None:
            return None

        return self._linha_para_medicao_persistida(linha)

    def marcar_como_enviado(self, ids_medicoes: List[int]) -> int:
        """Marca os IDs informados como ENVIADO e registra o instante da confirmação."""
        ids_validos = self._filtrar_ids_validos(ids_medicoes)
        if not ids_validos:
            return 0

        enviado_em = self._agora_iso()
        marcadores = ",".join(["?"] * len(ids_validos))

        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                f"""
                UPDATE medicoes
                SET
                    status_sync = ?,
                    enviado_em = ?,
                    ultimo_erro = NULL
                WHERE id IN ({marcadores})
                """,
                [STATUS_ENVIADO, enviado_em, *ids_validos],
            )

            conexao.commit()
            return int(cursor.rowcount)

    def registrar_falha_envio(self, ids_medicoes: List[int], mensagem_erro: str) -> int:
        """
        Mantém os registros como PENDENTE, incrementa tentativas e salva o último erro.
        Esse comportamento segue a regra atual da arquitetura.
        """
        ids_validos = self._filtrar_ids_validos(ids_medicoes)
        if not ids_validos:
            return 0

        if not mensagem_erro or not mensagem_erro.strip():
            raise ValueError("A mensagem de erro não pode ser vazia.")

        marcadores = ",".join(["?"] * len(ids_validos))

        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                f"""
                UPDATE medicoes
                SET
                    tentativas_envio = tentativas_envio + 1,
                    ultimo_erro = ?
                WHERE id IN ({marcadores})
                """,
                [mensagem_erro.strip(), *ids_validos],
            )

            conexao.commit()
            return int(cursor.rowcount)

    def contar_medicoes(self) -> int:
        """Retorna a quantidade total de medições salvas no banco."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT COUNT(*) FROM medicoes")
            resultado = cursor.fetchone()

        return int(resultado[0])

    def listar_todas(self) -> List[MedicaoPersistida]:
        """Retorna todas as medições salvas, ordenadas por ID."""
        with sqlite3.connect(self.caminho_banco) as conexao:
            conexao.row_factory = sqlite3.Row
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    data_hora,
                    pulsos,
                    chuva_intervalo_mm,
                    chuva_acumulada_mm,
                    status_sync,
                    tentativas_envio,
                    criado_em,
                    enviado_em,
                    ultimo_erro
                FROM medicoes
                ORDER BY id ASC
                """
            )

            linhas = cursor.fetchall()

        return [self._linha_para_medicao_persistida(linha) for linha in linhas]

    def _validar_medicao(self, medicao: Medicao) -> None:
        """Valida os dados básicos da medição antes da persistência."""
        if medicao.pulsos < 0:
            raise ValueError("O número de pulsos não pode ser negativo.")

        if medicao.chuva_intervalo_mm < 0:
            raise ValueError("A chuva do intervalo não pode ser negativa.")

        if medicao.chuva_acumulada_mm < 0:
            raise ValueError("A chuva acumulada não pode ser negativa.")

        if not medicao.data_hora or not medicao.data_hora.strip():
            raise ValueError("O campo data_hora é obrigatório.")

    def _filtrar_ids_validos(self, ids_medicoes: List[int]) -> List[int]:
        """Remove IDs inválidos, duplicados e preserva apenas inteiros positivos."""
        ids_ordenados_sem_duplicidade = []

        for item in ids_medicoes:
            if isinstance(item, int) and item > 0 and item not in ids_ordenados_sem_duplicidade:
                ids_ordenados_sem_duplicidade.append(item)

        return ids_ordenados_sem_duplicidade

    def _linha_para_medicao_persistida(self, linha: sqlite3.Row) -> MedicaoPersistida:
        """Converte uma linha do banco em objeto de domínio."""
        return MedicaoPersistida(
            id=int(linha["id"]),
            data_hora=str(linha["data_hora"]),
            pulsos=int(linha["pulsos"]),
            chuva_intervalo_mm=float(linha["chuva_intervalo_mm"]),
            chuva_acumulada_mm=float(linha["chuva_acumulada_mm"]),
            status_sync=str(linha["status_sync"]),
            tentativas_envio=int(linha["tentativas_envio"]),
            criado_em=str(linha["criado_em"]),
            enviado_em=linha["enviado_em"],
            ultimo_erro=linha["ultimo_erro"],
        )

    def _agora_iso(self) -> str:
        """Gera timestamp em formato ISO para facilitar leitura e integração futura."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _garantir_diretorio_banco(self) -> None:
        """Cria a pasta do banco caso ela ainda não exista."""
        self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)