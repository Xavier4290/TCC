import mysql.connector

conexaoMySQL = mysql.connector.connect(
    host='127.0.0.1',      # endereço do servidor
    user='root',           # nome de usuário do MySQL
    password='',  # senha do MySQL
    database='Pluvio'  # nome do banco que você quer usar
)

if conexaoMySQL.is_connected(): 
    print("Conectado ao banco de dados com sucesso")
    
    
class AlertaDeChuva:
    
    def Alerta(localizacao_latitude, localizacao_longitude):
            lat = float(localizacao_latitude)
            lon = float(localizacao_longitude)
            print("Alerta! Risco de alagamento")
            
            if lat < 0 and lon < 0:
                print("Alerta! Risco de alagamento")
           
            

