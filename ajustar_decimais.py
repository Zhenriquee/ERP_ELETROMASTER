from src.app import aplicacao
from src.extensoes import banco_de_dados as db
from sqlalchemy import text

def ajustar():
    with aplicacao.app_context():
        print("--- AJUSTANDO CASAS DECIMAIS ---")
        try:
            with db.engine.connect() as conn:
                # Altera o tipo das colunas para 3 casas decimais
                conn.execute(text("ALTER TABLE produtos_estoque ALTER COLUMN consumo_por_m2 TYPE NUMERIC(10, 3);"))
                conn.execute(text("ALTER TABLE produtos_estoque ALTER COLUMN consumo_por_m3 TYPE NUMERIC(10, 3);"))
                conn.execute(text("ALTER TABLE produtos_estoque ALTER COLUMN quantidade_atual TYPE NUMERIC(10, 3);"))
                conn.execute(text("ALTER TABLE produtos_estoque ALTER COLUMN quantidade_minima TYPE NUMERIC(10, 3);"))
                conn.commit()
            print("Sucesso: Colunas ajustadas para 3 casas decimais.")
        except Exception as e:
            print(f"Erro (pode ser que já esteja ajustado): {e}")

if __name__ == "__main__":
    ajustar()