from src.fabrica import criar_app

# Cria a aplicação usando a configuração de desenvolvimento
aplicacao = criar_app('desenvolvimento')

if __name__ == "__main__":
    # O host='0.0.0.0' permite acesso por outros PCs na rede local da empresa
    aplicacao.run(host='0.0.0.0', port=5000)