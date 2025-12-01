from Class.conexaoComDB import conexaoComDB
from datetime import datetime, timedelta



# conexaoComDB.enviaDadosParaTabelaSensor('SEN011',
#             'Pluviômetro',
#             -23.550520,
#             -46.633308,
#             'Av. Paulista, São Paulo - SP',
#             '2024-05-12 14:30:00',
#             True);


hoje = datetime.today()
ontem = hoje - timedelta(days=1)

#deleta a informação do banco no dia seguinte
# if hoje > ontem:
#     conexaoComDB.deletarInformacaoDoBanco('SEN011');
#     print("Arquivo deletado")

caminhoDoArquivo = r"C:\Users\guilh\Desktop\arquivos_TXT_para_teste\dadosRespbarry.txt"

with open(caminhoDoArquivo, "r", encoding="utf-8") as f:
    for linha in f:
        linha = linha.strip() #remove os espaços da linha
        coluna = linha.split(';') #Transforma os campos em lista
        print(coluna)
        conexaoComDB.enviaDadosParaTabelaSensor(*coluna)

print(linha)
print(len(coluna))


conexaoComDB.selecionarTabela(); #mostras as informações que estão dentro da tabela do banco de dados



