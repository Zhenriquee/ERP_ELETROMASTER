from src.app import aplicacao
from src.extensoes import banco_de_dados as db
from sqlalchemy import text

def reparar():
    with aplicacao.app_context():
        print("--- INICIANDO REPARO DO BANCO DE DADOS ---")
        
        # 1. Forçar criação das colunas de Preço em Produtos
        try:
            print("Verificando tabela produtos_estoque...")
            # Tenta adicionar as colunas se elas não existirem
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE produtos_estoque ADD COLUMN IF NOT EXISTS preco_m2 NUMERIC(10, 2) DEFAULT 0.00;"))
                conn.execute(text("ALTER TABLE produtos_estoque ADD COLUMN IF NOT EXISTS preco_m3 NUMERIC(10, 2) DEFAULT 0.00;"))
                conn.execute(text("ALTER TABLE produtos_estoque ADD COLUMN IF NOT EXISTS consumo_por_m2 NUMERIC(10, 4) DEFAULT 0.0000;"))
                conn.execute(text("ALTER TABLE produtos_estoque ADD COLUMN IF NOT EXISTS consumo_por_m3 NUMERIC(10, 4) DEFAULT 0.0000;"))
                conn.commit()
            print(" -> Colunas de Produto verificadas/criadas.")
        except Exception as e:
            print(f"Erro ao reparar produtos: {e}")

        # 2. Forçar criação das colunas em Itens da Venda
        try:
            print("Verificando tabela venda_itens...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE venda_itens ADD COLUMN IF NOT EXISTS metragem_total NUMERIC(10, 3) DEFAULT 0.000;"))
                conn.execute(text("ALTER TABLE venda_itens ADD COLUMN IF NOT EXISTS tipo_medida VARCHAR(5) DEFAULT 'm2';"))
                conn.commit()
            print(" -> Colunas de Venda verificadas/criadas.")
        except Exception as e:
            print(f"Erro ao reparar vendas: {e}")

        print("--- REPARO CONCLUÍDO ---")
        print("Agora reinicie o sistema e tente editar um produto.")

if __name__ == "__main__":
    reparar()