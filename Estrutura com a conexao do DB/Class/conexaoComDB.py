import psycopg2

conexaoPostgre = psycopg2.connect(
    host='100.74.148.84',      # endereço do servidor
    user='postgres',           # nome de usuário do MySQL
    password='1234',  # senha do MySQL
    database='Pluvio'  # nome do banco que você quer usar
)

if conexaoPostgre.closed == 0: 
    print("Conectado ao banco de dados com sucesso")
    
class conexaoComDB:
    def __init__(self, conexao):
        self.conexao = conexaoPostgre
    
    def enviaDadosParaTabelaSensor(data_hora, quantidade_ativacoes, chuva_acumulada_mm = 0): #Futuramente, será adicionado parâmentros nessa função
        cursor = conexaoPostgre.cursor()

        #Vai receber o insert e os valores que vão ser recebidos
        medicoes_pluviometro = """ 
        INSERT INTO medicoes_pluviometro
        (data_hora, quantidade_ativacoes, chuva_acumulada_mm)
        VALUES (%s, %s, %s) """ 
        
        # dadosTXT_teste = 
        # INSERT INTO dadosTXT_teste
        # (dadosTXT)
        # VALUES (%s)
        # """
        
        #a tupla valores será adicionada no banco de dados
        valores_dinamicos = (
          data_hora, 
          quantidade_ativacoes, 
          chuva_acumulada_mm
         )
       
        cursor.execute(medicoes_pluviometro, valores_dinamicos) #Executa o insert
        conexaoPostgre.commit() #Envia as informações para o banco
        cursor.close() #Fecha a conexão
        
        
    def deletarInformacaoDoBanco(sensor_id):
        
        cursor = conexaoPostgre.cursor()
        
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
        conexaoPostgre.commit()
        
        cursor.close()
        
 # Seleciona todas as informações na tabela
    def selecionarTabela():
        cursor = conexaoPostgre.cursor()
        cursor.execute("""
            SELECT 
                id,
                TO_CHAR(data_hora, 'DD/MM/YYYY HH24:MI:SS'),
                quantidade_ativacoes::float,
                chuva_acumulada_mm::float
            FROM medicoes_pluviometro;
            """)
        resultado = cursor.fetchall()
        for linha in resultado:
           print(linha)
            
#Funções temporárias 
    def deletarTablea(): 
        cursor = conexaoPostgre.cursor() 
        cursor.execute("DROP TABLE medicoes_pluviometro") 
        conexaoPostgre.commit() 
        cursor.close()
        
    def criarTabela():
        cursor = conexaoPostgre.cursor()
        cursor.execute("""
        CREATE TABLE medicoes_pluviometro (
            id SERIAL PRIMARY KEY,
            data_hora TIMESTAMP NOT NULL,
            quantidade_ativacoes NUMERIC(5,2),
            chuva_acumulada_mm NUMERIC(5,2)
        );
    """)
        conexaoPostgre.commit()
        cursor.close()