import mysql.connector
import pandas as pd
import os
from datetime import datetime
import subprocess

# ===============================
# 🔧 CONFIGURAÇÕES
# ===============================
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'Pluvio'
}

# Salva os dados no banco dados e transforma em um arquivo CSV. Cria um pasta chamada backup dentro da nuvem 
TABELA = 'Sensores'
NOME_ARQUIVO = f"backup_{TABELA}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
CAMINHO_LOCAL = os.path.abspath(NOME_ARQUIVO)
MEGA_CMD_PATH = r"C:\Users\guilh\AppData\Local\MEGAcmd\mega-put"
PASTA_MEGA = "/Backups"  # pasta no MEGA (será criada se não existir)
PASTA_BACKUP = "backup"

class conexaoMega:
    def __init__(self, db_config, tabela, pasta_mega, mega_cmd_path, pasta_backup):
        
        self.db_config = db_config
        self.tabela = tabela
        self.pasta_mega = pasta_mega
        self.mega_cmd_path = mega_cmd_path
        self.nome_arquivo = f"backup_{tabela}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.pasta_backup = pasta_backup

        # garante que a pasta exista
        os.makedirs(self.pasta_backup, exist_ok=True)

        # monta o caminho correto do arquivo
        self.caminho_local = os.path.abspath(
            os.path.join(self.pasta_backup, self.nome_arquivo)
        )

        self.conexao = None

    # ===========================
    # 🔗 Conexão com o MySQL
    # ===========================
    def conectar_banco(self):
        print("🔗 Conectando ao banco MySQL...")
        self.conexao = mysql.connector.connect(**self.db_config)

    # ===========================
    # 💾 Exportar tabela para CSV
    # ===========================
    def exportar_csv(self):
        print(f"📦 Exportando tabela '{self.tabela}' para CSV...")
        df = pd.read_sql(f"SELECT * FROM {self.tabela}", self.conexao)
        df.to_csv(self.caminho_local, index=False)
        print(f"✅ Arquivo criado: {self.caminho_local}")

    # ===========================
    # ☁️ Enviar arquivo ao MEGA
    # ===========================
    def enviar_para_mega(self):
        print("📤 Enviando arquivo para o MEGA.nz...")
        comando_upload = [self.mega_cmd_path, self.caminho_local, self.pasta_mega]
        resultado = subprocess.run(comando_upload, shell=True, capture_output=True, text=True)

        if resultado.returncode == 0:
            print(f"✅ Upload concluído com sucesso: {self.nome_arquivo}")
        else:
            print(f"⚠️ Erro no upload: {resultado.stderr}")

    # ===========================
    # 🔒 Encerrar conexão
    # ===========================
    def fechar_conexao(self):
        if self.conexao and self.conexao.is_connected():
            self.conexao.close()
            print("🔒 Conexão MySQL encerrada.")

    # ===========================
    # 🚀 Executar processo completo
    # ===========================
    def executar_backup(self):
        try:
            self.conectar_banco()
            self.exportar_csv()
            self.enviar_para_mega()
        except Exception as e:
            print(f"❌ Ocorreu um erro: {e}")
        finally:
            self.fechar_conexao()
# ===============================
# Definindo BackupBanco como subclasse/alias de conexaoMega
# ===============================
class BackupBanco(conexaoMega):
    """Alias/subclasse de conexaoMega para compatibilidade com o nome usado no main."""
    pass

# ===============================
# ▶️ EXECUÇÃO
# ===============================
if __name__ == "__main__":
    backup = BackupBanco(DB_CONFIG, TABELA, PASTA_MEGA, MEGA_CMD_PATH, PASTA_BACKUP)
    backup.executar_backup()