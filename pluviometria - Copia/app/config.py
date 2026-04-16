from pathlib import Path


# Diretório raiz do projeto.
BASE_DIR = Path(__file__).resolve().parent.parent

# Pasta usada para armazenar banco local e arquivos auxiliares.
DATA_DIR = BASE_DIR / "data"

# Caminho padrão do banco SQLite local.
CAMINHO_BANCO_SQLITE = DATA_DIR / "pluviometria_local.db"

# Configurações já definidas no planejamento arquitetural.
INTERVALO_MEDICAO_SEGUNDOS = 15
LIMITE_LOTE_SINCRONIZACAO = 10
INTERVALO_VERIFICACAO_PENDENCIAS_SEGUNDOS = 5
TEMPO_MAXIMO_ESPERA_ENVIO_SEGUNDOS = 30
MM_POR_PULSO = 0.25

# Modo de simulação:
# False = usa padrão fixo e repetitivo
# True = gera pulsos aleatórios a cada coleta
USAR_PULSOS_ALEATORIOS = True

# Padrão fixo para testes reprodutíveis.
PADRAO_PULSOS_SIMULADOS = (0, 1, 0, 2, 4, 0, 3, 0, 0, 6)

# Faixa aceitável de pulsos aleatórios por intervalo de 15 segundos.
PULSO_MINIMO_SIMULADO = 0
PULSO_MAXIMO_SIMULADO = 12

# Pesos usados no sorteio aleatório.
# Índice 0 -> peso do pulso 0
# Índice 1 -> peso do pulso 1
# ...
# Índice 12 -> peso do pulso 12
#
# A ideia é favorecer ausência de chuva e chuva fraca/moderada,
# deixando picos intensos mais raros.
PESOS_PULSOS_SIMULADOS = (
    20,  # 0 pulsos
    18,  # 1
    15,  # 2
    12,  # 3
    10,  # 4
    8,   # 5
    6,   # 6
    4,   # 7
    3,   # 8
    2,   # 9
    1,   # 10
    1,   # 11
    1,   # 12
)

# Configurações de rede para desenvolvimento local.
HOST_SERVIDOR_PC = "127.0.0.1"
PORTA_SERVIDOR_PC = 5000
TIMEOUT_SOCKET_SEGUNDOS = 10

# Estados atuais do fluxo de sincronização.
STATUS_PENDENTE = "PENDENTE"
STATUS_ENVIADO = "ENVIADO"