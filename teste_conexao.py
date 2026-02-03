from src.app import aplicacao
from src.extensoes import banco_de_dados
from src.modulos.autenticacao.modelos import Usuario

# Inicia o contexto da aplicação para ter acesso ao Banco
with aplicacao.app_context():
    print("--- CRIANDO USUÁRIO MASTER ---")
    
    # 1. Verifica se já existe
    usuario_existente = Usuario.query.filter_by(usuario='admin').first()
    
    if usuario_existente:
        print("AVISO: O usuário 'admin' já existe no banco de dados.")
        
        # Opcional: Se quiser resetar a senha dele, descomente abaixo:
        # usuario_existente.definir_senha('admin123')
        # banco_de_dados.session.commit()
        # print("Senha resetada para: admin123")
        
    else:
        # 2. Cria o novo usuário Dono
        novo_dono = Usuario()
        novo_dono.nome = "Administrador Master"
        novo_dono.usuario = "admin"
        novo_dono.email = "admin@eletromaster.com"
        novo_dono.cargo = "dono" # O cargo 'dono' tem acesso total no código
        novo_dono.ativo = True
        
        # Define a senha (Criptografada)
        novo_dono.definir_senha("admin123")
        
        # Salva no banco
        banco_de_dados.session.add(novo_dono)
        banco_de_dados.session.commit()
        
        print("SUCESSO: Usuário Master criado!")
        print("--------------------------------")
        print("Usuario: admin")
        print("Senha:   admin123")
        print("--------------------------------")