import psycopg2

conexaoPostgre = psycopg2.connect(
    host='100.74.148.84',      # endereço do servidor
    user='postgres',           # nome de usuário do MySQL
    password='1234',  # senha do MySQL
    database='Pluvio'  # nome do banco que você quer usar
)

if conexaoPostgre.closed == 0: 
    print("Conectado ao banco de dados com sucesso")
    
    
class AlertaDeChuva:
    
    def Alerta(localizacao_latitude, localizacao_longitude):
            lat = float(localizacao_latitude) 
            lon = float(localizacao_longitude)
            print("Alerta! Risco de alagamento")
            
            if lat < 0 and lon < 0:
                print("Alerta! Risco de alagamento")
           
            

