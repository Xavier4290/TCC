from pathlib import Path

from app.config import CAMINHO_BANCO_SQLITE, DATA_DIR


def remover_arquivo(caminho: Path) -> None:
    """Remove o arquivo informado, se ele existir."""
    if caminho.exists():
        caminho.unlink()
        print(f"Removido: {caminho}")
    else:
        print(f"Não encontrado: {caminho}")


def main() -> None:
    """Remove os bancos usados no desenvolvimento e nos testes locais."""
    arquivos_para_remover = [
        Path(CAMINHO_BANCO_SQLITE),
        DATA_DIR / "teste_coleta_simulada.db",
        DATA_DIR / "teste_sincronizacao.db",
    ]

    print("Limpando bases locais de desenvolvimento...\n")

    for caminho in arquivos_para_remover:
        remover_arquivo(caminho)

    print("\nLimpeza concluída.")


if __name__ == "__main__":
    main()