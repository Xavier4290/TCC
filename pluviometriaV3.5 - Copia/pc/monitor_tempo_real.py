import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
from matplotlib import animation

from app.config import CAMINHO_BANCO_CENTRAL_PC


FORMATO_DATA = "%Y-%m-%d %H:%M:%S"

MAPA_CLASSIFICACAO = {
    "sem_chuva": 0,
    "leve": 1,
    "moderada": 2,
    "forte": 3,
    "muito_intensa": 4,
}

ROTULOS_CLASSIFICACAO = [
    "sem",
    "leve",
    "mod",
    "forte",
    "m.intensa",
]

MAPA_NIVEL_ALERTA = {
    "sem_alerta": 0,
    "pre_alerta": 1,
    "atencao": 2,
    "alerta_moderado": 3,
    "alerta_alto": 4,
}

ROTULOS_ALERTA = [
    "sem",
    "pré",
    "atenção",
    "mod",
    "alto",
]


class MonitorTempoRealPluviometria:
    """
    Monitor gráfico simplificado em layout 2x2.

    Foco:
    - uma informação principal por gráfico;
    - fundo escuro;
    - resumo textual centralizado no topo;
    - sem eixos duplos;
    - menos poluição visual.
    """

    def __init__(
        self,
        caminho_banco: Path | str = CAMINHO_BANCO_CENTRAL_PC,
        limite_medicoes: int = 30,
        limite_analises: int = 20,
        limite_alertas: int = 20,
        intervalo_atualizacao_ms: int = 2000,
    ) -> None:
        self.caminho_banco = Path(caminho_banco)
        self.limite_medicoes = limite_medicoes
        self.limite_analises = limite_analises
        self.limite_alertas = limite_alertas
        self.intervalo_atualizacao_ms = intervalo_atualizacao_ms

        self._validar_configuracao()

        self.figura, eixos = plt.subplots(2, 2, figsize=(16, 9))
        self.ax_chuva = eixos[0][0]
        self.ax_pulsos = eixos[0][1]
        self.ax_classificacao = eixos[1][0]
        self.ax_alerta = eixos[1][1]

        self._textos_resumo = []
        self.animacao = None

        self._aplicar_tema_escuro_global()
        self.figura.subplots_adjust(
            top=0.82,
            bottom=0.10,
            left=0.09,
            right=0.98,
            hspace=0.42,
            wspace=0.18,
        )

    def executar(self) -> None:
        """Inicia a atualização gráfica contínua."""
        self.animacao = animation.FuncAnimation(
            self.figura,
            self._atualizar,
            interval=self.intervalo_atualizacao_ms,
            cache_frame_data=False,
        )
        plt.show()

    def _atualizar(self, _frame: int) -> None:
        """Atualiza os gráficos e o resumo superior."""
        medicoes = self._ler_medicoes()
        analises = self._ler_analises()
        alertas = self._ler_alertas()

        self._limpar_eixos()
        self._desenhar_resumo(medicoes, analises, alertas)
        self._desenhar_chuva_intervalo(medicoes)
        self._desenhar_pulsos(medicoes)
        self._desenhar_classificacao(analises)
        self._desenhar_nivel_alerta(alertas)

        self.figura.suptitle(
            f"Monitor de Pluviometria - última atualização: "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            fontsize=16,
            color="white",
            y=0.965,
        )

    def _limpar_eixos(self) -> None:
        """Limpa os eixos e remove o resumo textual anterior."""
        self.ax_chuva.clear()
        self.ax_pulsos.clear()
        self.ax_classificacao.clear()
        self.ax_alerta.clear()

        for texto in self._textos_resumo:
            texto.remove()
        self._textos_resumo = []

    def _ler_medicoes(self) -> List[dict]:
        """Lê as últimas medições brutas do banco central."""
        consulta = """
            SELECT
                id_origem,
                data_hora,
                pulsos,
                chuva_intervalo_mm,
                chuva_acumulada_mm
            FROM medicoes_recebidas
            ORDER BY id_origem DESC
            LIMIT ?
        """
        return self._executar_consulta(consulta, self.limite_medicoes)

    def _ler_analises(self) -> List[dict]:
        """Lê as últimas análises persistidas."""
        consulta = """
            SELECT
                id_ultima_medicao_origem,
                data_hora_ultima_medicao,
                classificacao_chuva,
                severidade_operacional,
                score_confianca,
                tendencia_final,
                sinal_pre_alerta
            FROM analises_chuva
            ORDER BY id_ultima_medicao_origem DESC
            LIMIT ?
        """
        return self._executar_consulta(consulta, self.limite_analises)

    def _ler_alertas(self) -> List[dict]:
        """Lê os alertas com ciclo de vida."""
        consulta = """
            SELECT
                id,
                status_alerta,
                nivel_alerta_atual,
                nivel_alerta_maximo,
                quantidade_atualizacoes,
                data_hora_ultima_medicao,
                aberto_em,
                atualizado_em,
                encerrado_em
            FROM alertas_evento
            ORDER BY id DESC
            LIMIT ?
        """
        return self._executar_consulta(consulta, self.limite_alertas)

    def _executar_consulta(self, consulta: str, limite: int) -> List[dict]:
        """Executa consulta e devolve registros em ordem cronológica crescente."""
        try:
            with sqlite3.connect(self.caminho_banco, timeout=2) as conexao:
                conexao.row_factory = sqlite3.Row
                cursor = conexao.cursor()
                cursor.execute(consulta, (limite,))
                linhas = cursor.fetchall()

            return [dict(linha) for linha in reversed(linhas)]

        except sqlite3.OperationalError:
            return []

    def _desenhar_resumo(
        self,
        medicoes: List[dict],
        analises: List[dict],
        alertas: List[dict],
    ) -> None:
        """Desenha resumo textual centralizado no topo."""
        ultima_medicao = medicoes[-1] if medicoes else None
        ultima_analise = analises[-1] if analises else None
        ultimo_alerta = alertas[-1] if alertas else None

        linha_1 = "Sem medições recentes."
        linha_2 = "Sem análises ou alertas recentes."

        if ultima_medicao:
            linha_1 = (
                f"Última medição | data_hora={ultima_medicao['data_hora']} | "
                f"pulsos={ultima_medicao['pulsos']} | "
                f"intervalo_mm={ultima_medicao['chuva_intervalo_mm']} | "
                f"acumulado_mm={ultima_medicao['chuva_acumulada_mm']}"
            )

        partes = []
        if ultima_analise:
            partes.extend(
                [
                    f"classificacao={ultima_analise['classificacao_chuva']}",
                    f"severidade={ultima_analise['severidade_operacional']}",
                    f"confianca={ultima_analise['score_confianca']}",
                    f"tendencia={ultima_analise['tendencia_final']}",
                ]
            )

        if ultimo_alerta:
            partes.extend(
                [
                    f"status_alerta={ultimo_alerta['status_alerta']}",
                    f"nivel_alerta={ultimo_alerta['nivel_alerta_atual']}",
                    f"nivel_maximo={ultimo_alerta['nivel_alerta_maximo']}",
                    f"atualizacoes={ultimo_alerta['quantidade_atualizacoes']}",
                ]
            )

        if partes:
            linha_2 = " | ".join(partes)

        texto_1 = self.figura.text(
            0.5,
            0.92,
            linha_1,
            color="white",
            fontsize=11,
            ha="center",
            va="center",
        )
        texto_2 = self.figura.text(
            0.5,
            0.885,
            linha_2,
            color="white",
            fontsize=11,
            ha="center",
            va="center",
        )

        self._textos_resumo.extend([texto_1, texto_2])

    def _desenhar_chuva_intervalo(self, medicoes: List[dict]) -> None:
        """Desenha a chuva por intervalo em gráfico de linha."""
        self._tema_eixo(self.ax_chuva, "Chuva por intervalo")
        self.ax_chuva.set_ylabel("mm", color="white")

        if not medicoes:
            self.ax_chuva.text(
                0.5,
                0.5,
                "Sem medições.",
                ha="center",
                va="center",
                color="white",
            )
            return

        tempos = [self._parse_data(m["data_hora"]) for m in medicoes]
        valores = [float(m["chuva_intervalo_mm"]) for m in medicoes]

        self.ax_chuva.plot(
            tempos,
            valores,
            marker="o",
            linewidth=2,
            label="chuva_intervalo_mm",
            color="#1f77b4",
        )

        self._aplicar_legenda(self.ax_chuva)
        self.ax_chuva.tick_params(axis="x", labelrotation=30, colors="white")
        
    def _desenhar_pulsos(self, medicoes: List[dict]) -> None:
        """Desenha pulsos por intervalo em gráfico de linha."""
        self._tema_eixo(self.ax_pulsos, "Pulsos por intervalo")
        self.ax_pulsos.set_ylabel("pulsos", color="white")

        if not medicoes:
            self.ax_pulsos.text(
                0.5,
                0.5,
                "Sem medições.",
                ha="center",
                va="center",
                color="white",
            )
            return

        tempos = [self._parse_data(m["data_hora"]) for m in medicoes]
        pulsos = [int(m["pulsos"]) for m in medicoes]

        self.ax_pulsos.plot(
            tempos,
            pulsos,
            marker="o",
            linewidth=2,
            label="pulsos",
            color="#ffcc00",
        )

        self._aplicar_legenda(self.ax_pulsos)
        self.ax_pulsos.tick_params(axis="x", labelrotation=30, colors="white")
  
    def _desenhar_classificacao(self, analises: List[dict]) -> None:
        """Desenha a classificação da chuva."""
        self._tema_eixo(self.ax_classificacao, "Classificação da chuva")

        if not analises:
            self.ax_classificacao.text(
                0.5,
                0.5,
                "Sem análises.",
                ha="center",
                va="center",
                color="white",
            )
            return

        tempos = [self._parse_data(a["data_hora_ultima_medicao"]) for a in analises]
        classificacao = [
            MAPA_CLASSIFICACAO.get(str(a["classificacao_chuva"]), 0) for a in analises
        ]

        self.ax_classificacao.step(
            tempos,
            classificacao,
            where="post",
            marker="o",
            linewidth=2,
            label="classificacao_chuva",
            color="#00ff99",
        )
        self.ax_classificacao.set_yticks(list(MAPA_CLASSIFICACAO.values()))
        self.ax_classificacao.set_yticklabels(ROTULOS_CLASSIFICACAO, color="white")
        self.ax_classificacao.tick_params(axis="y", labelsize=10, colors="white")
        self._aplicar_legenda(self.ax_classificacao)
        self.ax_classificacao.tick_params(axis="x", labelrotation=30, colors="white")

    def _desenhar_nivel_alerta(self, alertas: List[dict]) -> None:
        """Desenha o nível atual do alerta."""
        self._tema_eixo(self.ax_alerta, "Nível de alerta")

        if not alertas:
            self.ax_alerta.text(
                0.5,
                0.5,
                "Sem alertas.",
                ha="center",
                va="center",
                color="white",
            )
            return

        tempos = [self._parse_data(a["data_hora_ultima_medicao"]) for a in alertas]
        niveis = [
            MAPA_NIVEL_ALERTA.get(str(a["nivel_alerta_atual"]), 0) for a in alertas
        ]

        self.ax_alerta.step(
            tempos,
            niveis,
            where="post",
            marker="o",
            linewidth=2,
            label="nivel_alerta_atual",
            color="#ff4d6d",
        )
        self.ax_alerta.set_yticks(list(MAPA_NIVEL_ALERTA.values()))
        self.ax_alerta.set_yticklabels(ROTULOS_ALERTA, color="white")
        self.ax_alerta.tick_params(axis="y", labelsize=10, colors="white")
        self._aplicar_legenda(self.ax_alerta)
        self.ax_alerta.tick_params(axis="x", labelrotation=30, colors="white")

    def _aplicar_tema_escuro_global(self) -> None:
        """Aplica o tema escuro na figura."""
        self.figura.patch.set_facecolor("#000000")

    def _tema_eixo(self, eixo, titulo: str) -> None:
        """Aplica o tema escuro em um eixo."""
        eixo.set_facecolor("#0f0f0f")
        eixo.set_title(titulo, color="white")
        eixo.grid(True, alpha=0.16, color="#888888")
        eixo.tick_params(colors="white")

        for spine in eixo.spines.values():
            spine.set_color("#666666")

    def _aplicar_legenda(self, eixo) -> None:
        """Cria legenda com tema escuro."""
        legenda = eixo.legend(
            loc="upper left",
            frameon=True,
            facecolor="#111111",
            edgecolor="#444444",
        )

        if legenda is not None:
            for texto in legenda.get_texts():
                texto.set_color("white")

    def _parse_data(self, valor: str) -> datetime:
        """Converte string de data/hora para datetime."""
        return datetime.strptime(str(valor), FORMATO_DATA)

    def _validar_configuracao(self) -> None:
        """Valida os parâmetros básicos do monitor."""
        if self.limite_medicoes <= 0:
            raise ValueError("limite_medicoes deve ser maior que zero.")

        if self.limite_analises <= 0:
            raise ValueError("limite_analises deve ser maior que zero.")

        if self.limite_alertas <= 0:
            raise ValueError("limite_alertas deve ser maior que zero.")

        if self.intervalo_atualizacao_ms <= 0:
            raise ValueError("intervalo_atualizacao_ms deve ser maior que zero.")