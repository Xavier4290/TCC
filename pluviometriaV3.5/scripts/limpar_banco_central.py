from pc.repositorio_alertas_ciclo import RepositorioAlertasCicloSQLite
from pc.repositorio_analitico import RepositorioAnaliticoSQLite
from pc.repositorio_central import RepositorioCentralSQLite


def main() -> None:
    """Remove todos os registros brutos, analíticos e alertas da base central de desenvolvimento."""
    repositorio_central = RepositorioCentralSQLite()
    repositorio_central.inicializar_banco()

    repositorio_analitico = RepositorioAnaliticoSQLite()
    repositorio_analitico.inicializar_banco()

    repositorio_alertas = RepositorioAlertasCicloSQLite()
    repositorio_alertas.inicializar_banco()

    removidos_alertas = repositorio_alertas.remover_todos_alertas()
    removidos_analiticos = repositorio_analitico.remover_todas_analises()
    removidos_centrais = repositorio_central.remover_todos_registros()

    print(f"Alertas removidos da base central: {removidos_alertas}")
    print(f"Análises removidas da base central: {removidos_analiticos}")
    print(f"Registros brutos removidos da base central: {removidos_centrais}")


if __name__ == "__main__":
    main()