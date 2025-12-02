import mysql.connector

conexaoMySQL = mysql.connector.connect(
    host='127.0.0.1',      # endereço do servidor
    user='root',           # nome de usuário do MySQL
    password='',  # senha do MySQL
    database='Pluvio'  # nome do banco que você quer usar
)

if conexaoMySQL.is_connected(): 
    print("Conectado ao banco de dados com sucesso")
    
class conexaoComDB:
    def __init__(self, conexao):
        self.conexao = conexaoMySQL
    
    def enviaDadosParaTabelaSensor(sensor_id, tipo, localizacao_latitude, localizacao_longitude, localizacao_endereco, instalado_em, ativo): #Futuramente, será adicionado parâmentros nessa função
        cursor = conexaoMySQL.cursor()

        #Vai receber o insert e os valores que vão ser recebidos
        sensor = """ 
        INSERT INTO Sensores
        (sensor_id, tipo, localizacao_latitude, localizacao_longitude, localizacao_endereco, instalado_em, ativo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        # dadosTXT_teste = """ 
        # INSERT INTO dadosTXT_teste
        # (dadosTXT)
        # VALUES (%s)
        # """
        
        #a tupla valores será adicionada no banco de dados
        valores_dinamicos = (
            sensor_id,
            tipo,
            localizacao_latitude,
            localizacao_longitude,
            localizacao_endereco,
            instalado_em,
            ativo,
        )
        
       
        cursor.execute(sensor, valores_dinamicos) #Executa o insert
        conexaoMySQL.commit() #Envia as informações para o banco
        cursor.close() #Fecha a conexão
        
        
    def deletarInformacaoDoBanco(sensor_id):
        
        cursor = conexaoMySQL.cursor()
        
        #Deletar por tempo ou pelo ID ?
        # sql = "DELETE FROM Sensores WHERE sensor_id <= %s" #Código para deletar a informação da tabela
        # valores = (sensor_id,)
        
         # primeiro nas tabelas filhas
        cursor.execute("""
            DELETE FROM medicoespluviometricas
            WHERE CAST(SUBSTRING(sensor_id, 4) AS UNSIGNED) <= CAST(SUBSTRING(%s, 4) AS UNSIGNED)
        """, (sensor_id,))

        cursor.execute("""
            DELETE FROM dadosambientais
            WHERE CAST(SUBSTRING(sensor_id, 4) AS UNSIGNED) <= CAST(SUBSTRING(%s, 4) AS UNSIGNED)
        """, (sensor_id,))

        # depois na tabela pai
        cursor.execute("""
            DELETE FROM sensores
            WHERE CAST(SUBSTRING(sensor_id, 4) AS UNSIGNED) <= CAST(SUBSTRING(%s, 4) AS UNSIGNED)
        """, (sensor_id,))

        # cursor.execute(sql, valores)
        conexaoMySQL.commit()
        
        cursor.close()

     # Seleciona todas as informações na tabela
    def selecionarTabela():
        cursor = conexaoMySQL.cursor()
        cursor.execute("select * from Sensores;")
        resultado = cursor.fetchall()
        for linha in resultado:
            print(linha)