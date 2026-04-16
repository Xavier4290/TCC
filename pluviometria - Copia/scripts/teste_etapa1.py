from app.repositorio_medicoes import RepositorioMedicoesSQLite
from app.modelos import Medicao


def imprimir_titulo(texto: str) -> None:
    """Exibe um título simples para organizar a saída do teste."""
    print("\n" + "=" * 70)
    print(texto)
    print("=" * 70)


def imprimir_medicoes(medicoes) -> None:
    """Mostra as medições retornadas pelo repositório."""
    for medicao in medicoes:
        print(
            f"ID={medicao.id} | data_hora={medicao.data_hora} | "
            f"pulsos={medicao.pulsos} | intervalo={medicao.chuva_intervalo_mm:.2f} mm | "
            f"acumulado={medicao.chuva_acumulada_mm:.2f} mm | "
            f"status={medicao.status_sync} | tentativas={medicao.tentativas_envio} | "
            f"erro={medicao.ultimo_erro} | enviado_em={medicao.enviado_em}"
        )


def main() -> None:
    """Executa um fluxo simples de validação da camada SQLite."""
    repositorio = RepositorioMedicoesSQLite()
    repositorio.inicializar_banco()

    imprimir_titulo("Inserindo medições de teste")

    ids_criados = []
    ids_criados.append(
        repositorio.inserir_medicao(
            Medicao(
                data_hora="2026-04-12 10:00:00",
                pulsos=2,
                chuva_intervalo_mm=0.50,
                chuva_acumulada_mm=0.50,
            )
        )
    )
    ids_criados.append(
        repositorio.inserir_medicao(
            Medicao(
                data_hora="2026-04-12 10:00:15",
                pulsos=3,
                chuva_intervalo_mm=0.75,
                chuva_acumulada_mm=1.25,
            )
        )
    )
    ids_criados.append(
        repositorio.inserir_medicao(
            Medicao(
                data_hora="2026-04-12 10:00:30",
                pulsos=0,
                chuva_intervalo_mm=0.00,
                chuva_acumulada_mm=1.25,
            )
        )
    )

    print(f"IDs inseridos: {ids_criados}")
    print(f"Total de medições no banco: {repositorio.contar_medicoes()}")

    imprimir_titulo("Buscando pendentes")
    pendentes = repositorio.buscar_pendentes(limite=10)
    imprimir_medicoes(pendentes)

    imprimir_titulo("Registrando falha de envio para os dois primeiros IDs")
    quantidade_falhas = repositorio.registrar_falha_envio(
        ids_medicoes=ids_criados[:2],
        mensagem_erro="Falha simulada de conexão com o PC",
    )
    print(f"Registros atualizados com falha: {quantidade_falhas}")

    imprimir_titulo("Marcando o terceiro ID como enviado")
    quantidade_enviados = repositorio.marcar_como_enviado([ids_criados[2]])
    print(f"Registros marcados como enviados: {quantidade_enviados}")

    imprimir_titulo("Estado final das medições")
    todas = repositorio.listar_todas()
    imprimir_medicoes(todas)


if __name__ == "__main__":
    main()