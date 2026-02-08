from src.app import aplicacao
from src.extensoes import banco_de_dados as db
from src.modulos.corporativo.modelos import Setor, Cargo
from src.modulos.rh.modelos import Colaborador
from src.modulos.autenticacao.modelos import Usuario
from datetime import date

def criar_dados_iniciais():
    with aplicacao.app_context():
        print("--- INICIANDO CARGA DE DADOS ---")

        # 1. CRIAR SETOR
        setor_adm = Setor.query.filter_by(nome="Administração").first()
        if not setor_adm:
            setor_adm = Setor(nome="Administração", descricao="Diretoria e Gestão")
            db.session.add(setor_adm)
            db.session.flush() # Gera o ID
            print(f"Setor criado: {setor_adm.nome}")
        
        # 2. CRIAR CARGO (DONO)
        cargo_dono = Cargo.query.filter_by(nome="Dono").first()
        if not cargo_dono:
            cargo_dono = Cargo(
                nome="Dono",
                setor_id=setor_adm.id,
                nivel_hierarquico=1, # Nível Máximo
                descricao="Acesso total ao sistema"
            )
            db.session.add(cargo_dono)
            db.session.flush()
            print(f"Cargo criado: {cargo_dono.nome}")

        # 3. CRIAR COLABORADOR
        # O sistema precisa de uma pessoa física para vincular o usuário
        colab_admin = Colaborador.query.filter_by(cpf="000.000.000-00").first()
        if not colab_admin:
            colab_admin = Colaborador(
                nome_completo="Administrador Master",
                cpf="000.000.000-00", # CPF Fictício para o admin
                data_admissao=date.today(),
                cargo_id=cargo_dono.id,
                tipo_contrato="Socio",
                ativo=True
            )
            db.session.add(colab_admin)
            db.session.flush()
            print(f"Colaborador criado: {colab_admin.nome_completo}")

        # 4. CRIAR USUÁRIO DE ACESSO
        usuario_admin = Usuario.query.filter_by(usuario="admin").first()
        if not usuario_admin:
            usuario_admin = Usuario(
                usuario="admin",
                colaborador_id=colab_admin.id, # Vínculo Obrigatório
                ativo=True
            )
            usuario_admin.definir_senha("admin123") # SENHA PADRÃO
            
            db.session.add(usuario_admin)
            print(f"Usuário de acesso criado: admin")
        else:
            print("Usuário admin já existe.")

        db.session.commit()
        print("--- SUCESSO: ESTRUTURA INICIAL CRIADA ---")
        print("Login: admin")
        print("Senha: admin123")

if __name__ == "__main__":
    criar_dados_iniciais()