from src.fabrica import criar_app
import os

# Cria a aplicação usando a configuração de desenvolvimento
aplicacao = criar_app('desenvolvimento')

if __name__ == "__main__":
    # --- MUDANÇA PARA PRODUÇÃO (WAITRESS) ---
    from waitress import serve

    port = 5000
    print(f"--- SISTEMA INICIADO ---")
    print(f"Acesse em: http://localhost:{port}")
    print(f"Para fechar, feche esta janela.")

    # O Waitress aguenta múltiplas conexões e é estável para Windows
    serve(aplicacao, host='0.0.0.0', port=port, threads=6)