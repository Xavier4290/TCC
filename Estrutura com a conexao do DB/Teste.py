#Clase utilizada para teste. Em breve, será apagada

from Class.conexaoComDB import conexaoComDB
from Class.AlertaDeChuva import AlertaDeChuva
from Class.conexaoMega import conexaoMega
from datetime import datetime, timedelta
import glob

DB_CONFIG = {
    'host': '100.74.148.84',
    'user': 'postgres',
    'password': '1234',
    'database': 'Pluvio'
}

opcao = True
while opcao == True:
    op = int(input("Digite 1 para listar as informações do banco \n"+
                   "Digite 2 para enviar as informações para o banco\n"+
                   "Digite 3 para enviar as informações para a nuvem"))
    
    match op:
        case 1:
            conexaoComDB.selecionarTabela();
            
        case 2:
            #caminho do arquivo TXT
            caminhos = glob.glob(r"C:\Users\guilh\Desktop\arquivos_TXT_para_teste\*.txt") #Seleciona todos os arquivos txt que estiverem dentro da pasta

            #Permite a leitura do conteúdo do arquivo txt
            for caminhoDoArquivo in caminhos:
                with open(caminhoDoArquivo, "r", encoding="utf-8") as f:
                    for linha in f:
                        linha = linha.strip() #remove os espaços da linha
                        coluna = linha.split(';') #Transforma os campos em lista
                        print(coluna)
                        conexaoComDB.enviaDadosParaTabelaSensor(*coluna) #coloca o item da lista como parâmetros separados

            print(linha) #mostra a linha
            print(len(coluna)) #mostra o tamanho da coluna
            
        case 3:
            TABELA = 'Sensores'
            NOME_ARQUIVO = f"backup_{TABELA}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            MEGA_CMD_PATH = r"C:\Users\guilh\AppData\Local\MEGAcmd\mega-put"
            PASTA_MEGA = "/Backups"  # pasta no MEGA (será criada se não existir)
            PASTA_BACKUP = "backup"

            conMega = conexaoMega(
                db_config=DB_CONFIG,
                tabela=TABELA,
                pasta_mega=PASTA_MEGA,
                mega_cmd_path=MEGA_CMD_PATH,
                pasta_backup=PASTA_BACKUP
            )

            conMega.conectar_banco()
            conMega.exportar_csv()
            conMega.enviar_para_mega()
            
        case 4:
            conexaoComDB.deletarTabela()
            print("Tabela deletada com sucesso!")
        case _:
            print("Tchau, tchau!")