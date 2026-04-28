import psycopg2
from psycopg2.extensions import connection
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from psycopg2.extras import RealDictCursor

from .config import STATUS_ENVIADO, STATUS_PENDENTE, CONFIG_POSTGRES
from .modelos import Medicao, MedicaoPersistida


class RepositorioMedicoesSQLite:
    """Centraliza o acesso ao banco SQLite local de medições."""

    def __init__(self) -> None:
        self.conexao: connection = self._criar_conexao()

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
        """Cria a tabela principal e os índices necessários, caso não existam."""

        with self.conexao.cursor() as cursor:

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS medicoes (
                    id SERIAL PRIMARY KEY,
                    data_hora TIMESTAMP NOT NULL,
                    pulsos INTEGER NOT NULL CHECK (pulsos >= 0),
                    chuva_intervalo_mm DOUBLE PRECISION NOT NULL CHECK (chuva_intervalo_mm >= 0),
                    chuva_acumulada_mm DOUBLE PRECISION NOT NULL CHECK (chuva_acumulada_mm >= 0),

                    status_sync VARCHAR(20) NOT NULL DEFAULT 'PENDENTE'
                        CHECK (status_sync IN ('PENDENTE', 'ENVIADO')),

                    tentativas_envio INTEGER NOT NULL DEFAULT 0
                        CHECK (tentativas_envio >= 0),

                    criado_em TIMESTAMP NOT NULL,
                    enviado_em TIMESTAMP,
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
            
        self.conexao.commit()
        
    def fechar_conexao(self) -> None:
        """Fecha a conexão com o banco"""
        if self.conexao and self.conexao.closed == 0:
            self.conexao.close()

    def inserir_medicao(self, medicao: Medicao) -> int:
        """Insere uma nova medição no banco com status inicial PENDENTE."""

        self._validar_medicao(medicao)
        criado_em = self._agora()

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO medicoes (
                    data_hora,
                    pulsos,
                    chuva_intervalo_mm,
                    chuva_acumulada_mm,
                    status_sync,
                    tentativas_envio,
                    criado_em
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    medicao.data_hora,
                    medicao.pulsos,
                    medicao.chuva_intervalo_mm,
                    medicao.chuva_acumulada_mm,
                    STATUS_PENDENTE,
                    0,
                    criado_em
                )
            )

            id_inserido = cursor.fetchone()[0]

        self.conexao.commit()

        return id_inserido

    def buscar_pendentes(self, limite: int = 10) -> List[MedicaoPersistida]:
        """Retorna os registros pendentes mais antigos, respeitando o limite informado."""

        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        with self.conexao.cursor() as cursor:
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
                WHERE status_sync = %s
                ORDER BY id ASC
                LIMIT %s
                """,
                (STATUS_PENDENTE, limite),
            )

            colunas = [desc[0] for desc in cursor.description]
            linhas = cursor.fetchall()

        # Converter para dict (equivalente ao sqlite Row)
        resultados = [
            dict(zip(colunas, linha))
            for linha in linhas
        ]

        return [self._linha_para_medicao_persistida(linha) for linha in resultados]

    def contar_pendentes(self) -> int:
        """Retorna a quantidade total de registros ainda pendentes de sincronização."""

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM medicoes
                WHERE status_sync = %s
                """,
                (STATUS_PENDENTE,),
            )

            resultado = cursor.fetchone()

        return int(resultado[0])

    

    def buscar_pendente_mais_antigo(self) -> Optional[MedicaoPersistida]:
        """Retorna o registro pendente mais antigo, ou None quando não houver pendências."""

        with self.conexao.cursor(cursor_factory=RealDictCursor) as cursor:
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
                    WHERE status_sync = %s
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

        enviado_em = self._agora()

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                UPDATE medicoes
                SET
                    status_sync = %s,
                    enviado_em = %s,
                    ultimo_erro = NULL
                WHERE id = ANY(%s)
                """,
                (STATUS_ENVIADO, enviado_em, ids_validos),
            )

            linhas_afetadas = cursor.rowcount

        self.conexao.commit()

        return int(linhas_afetadas)

    def registrar_falha_envio(self, ids_medicoes: List[int], mensagem_erro: str) -> int:
        """
        Mantém os registros como PENDENTE, incrementa tentativas e salva o último erro.
        """

        ids_validos = self._filtrar_ids_validos(ids_medicoes)
        if not ids_validos:
            return 0

        if not mensagem_erro or not mensagem_erro.strip():
            raise ValueError("A mensagem de erro não pode ser vazia.")

        mensagem_limpa = mensagem_erro.strip()

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                UPDATE medicoes
                SET
                    tentativas_envio = tentativas_envio + 1,
                    ultimo_erro = %s
                WHERE id = ANY(%s)
                """,
                (mensagem_limpa, ids_validos),
            )

            linhas_afetadas = cursor.rowcount

        self.conexao.commit()

        return int(linhas_afetadas)

    def contar_medicoes(self) -> int:
        """Retorna a quantidade total de medições salvas no banco."""

        with self.conexao.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM medicoes")
            resultado = cursor.fetchone()

        return int(resultado[0]) if resultado else 0

    def listar_todas(self) -> List[MedicaoPersistida]:
        """Retorna todas as medições salvas, ordenadas por ID."""

        with self.conexao.cursor(cursor_factory=RealDictCursor) as cursor:
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

    def _linha_para_medicao_persistida(self, linha: dict) -> MedicaoPersistida:
        """Converte uma linha do banco em objeto de domínio."""

        return MedicaoPersistida(
            id=int(linha["id"]),
            data_hora=linha["data_hora"],  # já é datetime
            pulsos=int(linha["pulsos"]),
            chuva_intervalo_mm=float(linha["chuva_intervalo_mm"]),
            chuva_acumulada_mm=float(linha["chuva_acumulada_mm"]),
            status_sync=str(linha["status_sync"]),
            tentativas_envio=int(linha["tentativas_envio"]),
            criado_em=linha["criado_em"],  # datetime
            enviado_em=linha["enviado_em"],  # pode ser None
            ultimo_erro=linha["ultimo_erro"],
    )

    def _agora(self) -> datetime:
        """Retorna o timestamp atual como datetime."""
        return datetime.now()

    # def _garantir_diretorio_banco(self) -> None:
    #     """Cria a pasta do banco caso ela ainda não exista."""
    #     self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)
    
    def remover_medicoes_enviadas(self) -> int:
        """Remove do banco todas as medições com status ENVIADO."""

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM medicoes
                WHERE status_sync = %s
                """,
                (STATUS_ENVIADO,),
            )

            linhas_removidas = cursor.rowcount

        self.conexao.commit()

        return int(linhas_removidas)


    def remover_medicoes_pendentes(self) -> int:
        """Remove do banco todas as medições com status PENDENTE."""

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM medicoes
                WHERE status_sync = %s
                """,
                (STATUS_PENDENTE,),
            )

            linhas_removidas = cursor.rowcount

        self.conexao.commit()

        return int(linhas_removidas)


    def remover_todas_medicoes(self) -> int:
        """Remove todas as medições do banco."""

        with self.conexao.cursor() as cursor:
            cursor.execute("DELETE FROM medicoes")
            linhas_removidas = cursor.rowcount

        self.conexao.commit()

        return int(linhas_removidas)
        
    def remover_medicoes_enviadas_mais_antigas_que(self, data_limite: datetime) -> int:
        """
        Remove medições ENVIADAS cujo enviado_em seja anterior à data limite.
        """

        if not isinstance(data_limite, datetime):
            raise ValueError("data_limite deve ser um datetime válido.")

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM medicoes
                WHERE status_sync = %s
                AND enviado_em IS NOT NULL
                AND enviado_em < %s
                """,
                (STATUS_ENVIADO, data_limite),
            )

            linhas_removidas = cursor.rowcount

        self.conexao.commit()

        return int(linhas_removidas)
        
    def contar_medicoes_enviadas_mais_antigas_que(self, data_limite: datetime) -> int:
        """
        Conta medições ENVIADAS cujo enviado_em seja anterior à data limite.
        """

        if not isinstance(data_limite, datetime):
            raise ValueError("data_limite deve ser um datetime válido.")

        with self.conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM medicoes
                WHERE status_sync = %s
                AND enviado_em IS NOT NULL
                AND enviado_em < %s
                """,
                (STATUS_ENVIADO, data_limite),
            )

            resultado = cursor.fetchone()

        return int(resultado[0]) if resultado else 0