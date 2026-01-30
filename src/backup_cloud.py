import os
import gzip
import subprocess
from mega import Mega
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def realizar_backup_nuvem():
    # 1. VERIFICAÇÃO DE CICLO (1, 10, 20)
    hoje = datetime.now()
    dia_atual = hoje.day
    
    # Se NÃO for um dos dias escolhidos, encerra o script sem fazer nada
    # (Isso permite que o Agendador do Windows rode todo dia sem erro)
    dias_permitidos = [1, 10, 20]
    
    if dia_atual not in dias_permitidos:
        print(f"Hoje é dia {dia_atual}. Backup agendado apenas para dias {dias_permitidos}.")
        return False

    print(f"--- INICIANDO BACKUP DE CICLO (DIA {dia_atual}) ---")

    # 2. CONFIGURAÇÕES
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NOME', 'erp_eletromaster')
    DB_USER = os.getenv('DB_USUARIO', 'postgres')
    DB_PASS = os.getenv('DB_SENHA', '')
    
    MEGA_EMAIL = os.getenv('MEGA_EMAIL')
    MEGA_SENHA = os.getenv('MEGA_SENHA')
    
    # IMPORTANTE: Caminho do PG_DUMP no Windows
    PG_DUMP_EXE = os.getenv('PG_DUMP_PATH', r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe")

    # 3. NOME DO ARQUIVO (FIXO POR CICLO)
    # Ex: backup_ciclo_dia_10.sql.gz
    # Isso garante que no mês que vem, o nome será o mesmo e substituiremos o antigo
    nome_arquivo_base = f"backup_ciclo_dia_{dia_atual:02d}.sql.gz"
    
    caminho_sql = os.path.join(os.getcwd(), "temp_dump.sql")
    caminho_zip = os.path.join(os.getcwd(), nome_arquivo_base)

    try:
        # 4. EXECUTAR DUMP (Extrair dados do banco)
        print(f"1. Gerando Dump do banco...")
        env_dump = os.environ.copy()
        env_dump['PGPASSWORD'] = DB_PASS
        
        comando = [
            PG_DUMP_EXE, '-h', DB_HOST, '-U', DB_USER, '-d', DB_NAME, '-f', caminho_sql
        ]
        # check=True faz o python avisar se der erro no comando
        subprocess.run(comando, env=env_dump, check=True)
        
        # 5. COMPACTAR (Diminui o tamanho drasticamente)
        print("2. Compactando arquivo...")
        with open(caminho_sql, 'rb') as f_in:
            with gzip.open(caminho_zip, 'wb') as f_out:
                f_out.writelines(f_in)
        
        os.remove(caminho_sql) # Limpa o SQL bruto pesado

        # 6. UPLOAD COM SUBSTITUIÇÃO (Mega.nz)
        if MEGA_EMAIL and MEGA_SENHA:
            print("3. Conectando ao Mega.nz...")
            mega = Mega()
            m = mega.login(MEGA_EMAIL, MEGA_SENHA)
            
            # --- LÓGICA DE SUBSTITUIÇÃO ---
            # Procura se já existe um arquivo com esse nome lá na nuvem
            arquivo_antigo = m.find(nome_arquivo_base)
            
            if arquivo_antigo:
                print(f"   Encontrado backup antigo ({nome_arquivo_base}). Substituindo...")
                m.destroy(arquivo_antigo[0]) # Remove o arquivo antigo da nuvem
            
            # Faz o upload do novo
            print(f"   Enviando novo backup: {nome_arquivo_base}...")
            m.upload(caminho_zip)
            print("   Upload concluído com sucesso!")
        else:
            print("   AVISO: Credenciais do Mega não configuradas.")

        # Limpeza local final (Remove o arquivo do computador para não ocupar espaço)
        if os.path.exists(caminho_zip):
            os.remove(caminho_zip)
            
        print(f"--- BACKUP DO DIA {dia_atual} FINALIZADO ---")
        return True

    except Exception as e:
        print(f"ERRO CRÍTICO NO BACKUP: {e}")
        return False