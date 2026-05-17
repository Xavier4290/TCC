from app.config import CAMINHO_BANCO_SQLITE
from app.repositorio_medicoes import RepositorioMedicoesSQLite


def main() -> None:
    """Cria e inicializa o banco SQLite local principal do projeto."""
    repositorio = RepositorioMedicoesSQLite()
    repositorio.inicializar_banco()

    print("Banco local inicializado com sucesso.")
    print(f"Caminho: {CAMINHO_BANCO_SQLITE}")


if __name__ == "__main__":
    main()