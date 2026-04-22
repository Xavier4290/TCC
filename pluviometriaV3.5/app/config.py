from pathlib import Path



# Diretório raiz do projeto.
BASE_DIR = Path(__file__).resolve().parent.parent

# Pasta usada para armazenar banco local e arquivos auxiliares.
DATA_DIR = BASE_DIR / "data"

# Caminho padrão do banco SQLite local.
CAMINHO_BANCO_SQLITE = DATA_DIR / "pluviometria_local.db"

# Configuração do servidor postgre
CONFING_POSTGRE = {
    'host': '100.74.148.84',
    'user': 'postgres',
    'password': '1234',
    'database': 'Pluvio'
}

# Caminho do banco central usado no lado do PC durante o desenvolvimento.
CAMINHO_BANCO_CENTRAL_PC = DATA_DIR / "pluviometria_central_pc.db"

# Conexão com o banco postgres
CONFIG_POSTGRES = {
    "host": "100.74.148.84",
    "user": "postgres",
    "password": "1234",
    "database": "Pluvio"
}


# Configurações já definidas no planejamento arquitetural.
INTERVALO_MEDICAO_SEGUNDOS = 15
LIMITE_LOTE_SINCRONIZACAO = 10
INTERVALO_VERIFICACAO_PENDENCIAS_SEGUNDOS = 5
TEMPO_MAXIMO_ESPERA_ENVIO_SEGUNDOS = 30
MM_POR_PULSO = 0.25

# Política de manutenção local do banco no lado do Raspberry/cliente.
# Nesta fase, a manutenção automática ainda não será acoplada ao fluxo principal.
MANUTENCAO_LOCAL_HABILITADA = False

# Quantidade de horas para retenção local de registros ENVIADO.
# Registros enviados mais antigos que esse limite podem ser removidos.
RETENCAO_LOCAL_ENVIADOS_HORAS = 24

# Intervalo entre execuções da manutenção local automática.
INTERVALO_MANUTENCAO_LOCAL_SEGUNDOS = 300

# Configurações previstas para o modo GPIO no Raspberry Pi.
GPIO_PIN = 17
GPIO_BOUNCETIME_MS = 300

# Modo atual de execução:
# - "simulado": usa coleta artificial no PC
# - "gpio": reservado para futura coleta real no Raspberry
MODO_EXECUCAO = "simulado"

# Modo de simulação:
# False = usa padrão fixo e repetitivo
# True = gera pulsos aleatórios a cada coleta
USAR_PULSOS_ALEATORIOS = False

# Padrão fixo para testes reprodutíveis.
PADRAO_PULSOS_SIMULADOS = (0, 1, 2, 4, 6, 8, 5, 4, 3, 0, 0, 0)

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

# Configurações da camada analítica inicial no PC.
LIMITE_JANELA_ANALITICA = 6
MINIMO_MEDICOES_ANALISE = 4

# Regras de continuidade da janela analítica.
TOLERANCIA_CONTIGUIDADE_MEDICOES_SEGUNDOS = 5

# Se o acumulado atual cair abaixo do acumulado anterior, entendemos que houve
# reinício de contexto e a janela deve ser quebrada.
PERMITIR_REINICIO_ACUMULADO_NA_JANELA = False
