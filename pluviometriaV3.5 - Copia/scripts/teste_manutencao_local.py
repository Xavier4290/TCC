from datetime import datetime, timedelta
from pathlib import Path

from app.config import DATA_DIR, STATUS_ENVIADO, STATUS_PENDENTE
from app.manutencao_local import ManutencaoLocal
from app.modelos import Medicao
from app.repositorio_medicoes import RepositorioMedicoesSQLite


FORMATO_DATA = "%Y-%m-%d %H:%M:%S"


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída."""
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def preparar_banco_teste(caminho_banco: Path) -> None:
    """Remove o banco anterior para garantir execução limpa."""
    caminho_banco.parent.mkdir(parents=True, exist_ok=True)

    if caminho_banco.exists():
        caminho_banco.unlink()


def inserir_medicoes_base(repositorio: RepositorioMedicoesSQLite) -> None:
    """Insere medições simples para compor o cenário do teste."""
    medicoes = [
        Medicao(
            data_hora="2026-04-19 05:00:00",
            pulsos=2,
            chuva_intervalo_mm=0.50,
            chuva_acumulada_mm=0.50,
        ),
        Medicao(
            data_hora="2026-04-19 05:00:15",
            pulsos=3,
            chuva_intervalo_mm=0.75,
            chuva_acumulada_mm=1.25,
        ),
        Medicao(
            data_hora="2026-04-19 05:00:30",
            pulsos=1,
            chuva_intervalo_mm=0.25,
            chuva_acumulada_mm=1.50,
        ),
    ]

    for medicao in medicoes:
        repositorio.inserir_medicao(medicao)


def ajustar_cenario_teste(repositorio: RepositorioMedicoesSQLite) -> None:
    """
    Prepara o banco com:
    - 1 registro ENVIADO antigo
    - 1 registro ENVIADO recente
    - 1 registro PENDENTE
    """
    todas = repositorio.listar_todas()

    if len(todas) != 3:
        raise RuntimeError("O cenário de teste esperava exatamente 3 registros.")

    id_antigo = todas[0].id
    id_recente = todas[1].id
    id_pendente = todas[2].id

    repositorio.marcar_como_enviado([id_antigo, id_recente])

    agora = datetime.now()
    antigo = (agora - timedelta(hours=48)).strftime(FORMATO_DATA)
    recente = (agora - timedelta(hours=1)).strftime(FORMATO_DATA)

    caminho_banco = repositorio.caminho_banco

    import sqlite3
    with sqlite3.connect(caminho_banco) as conexao:
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE medicoes
            SET enviado_em = ?, status_sync = ?
            WHERE id = ?
            """,
            (antigo, STATUS_ENVIADO, id_antigo),
        )

        cursor.execute(
            """
            UPDATE medicoes
            SET enviado_em = ?, status_sync = ?
            WHERE id = ?
            """,
            (recente, STATUS_ENVIADO, id_recente),
        )

        cursor.execute(
            """
            UPDATE medicoes
            SET status_sync = ?, enviado_em = NULL
            WHERE id = ?
            """,
            (STATUS_PENDENTE, id_pendente),
        )

        conexao.commit()


def imprimir_registros(repositorio: RepositorioMedicoesSQLite) -> None:
    """Mostra os registros do banco para facilitar validação visual."""
    for medicao in repositorio.listar_todas():
        print(
            f"ID={medicao.id} | status={medicao.status_sync} | "
            f"data_hora={medicao.data_hora} | "
            f"enviado_em={medicao.enviado_em} | "
            f"tentativas={medicao.tentativas_envio}"
        )


def main() -> None:
    """Valida a manutenção local com retenção de enviados antigos."""
    caminho_banco_teste = DATA_DIR / "teste_manutencao_local.db"
    preparar_banco_teste(caminho_banco_teste)

    repositorio = RepositorioMedicoesSQLite(caminho_banco_teste)
    repositorio.inicializar_banco()

    inserir_medicoes_base(repositorio)
    ajustar_cenario_teste(repositorio)

    imprimir_titulo("Estado antes da manutenção")
    imprimir_registros(repositorio)

    manutencao = ManutencaoLocal(
        repositorio=repositorio,
        retencao_enviados_horas=24,
    )

    imprimir_titulo("Executando manutenção local")
    resultado = manutencao.executar_limpeza_enviados_antigos()
    print(resultado)

    imprimir_titulo("Estado depois da manutenção")
    imprimir_registros(repositorio)


if __name__ == "__main__":
    main()