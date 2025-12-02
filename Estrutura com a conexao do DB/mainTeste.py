from Class.conexaoComDB import conexaoComDB
from datetime import datetime, timedelta
import glob

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

conexaoComDB.selecionarTabela(); #mostras as informações que estão dentro da tabela do banco de dados

hoje = datetime.today()
ontem = hoje - timedelta(days=1)

#deleta a informação do banco no dia seguinte
if hoje > ontem:
    conexaoComDB.deletarInformacaoDoBanco(coluna[0]); #Deleta a informação pelo ID 
    print("Arquivo deletado")



