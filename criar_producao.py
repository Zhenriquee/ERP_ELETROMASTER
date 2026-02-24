from src.app import aplicacao
from src.extensoes import banco_de_dados as db
from src.modulos.corporativo.modelos import Setor, Cargo
from src.modulos.rh.modelos import Colaborador
from src.modulos.autenticacao.modelos import Usuario
from datetime import date

def criar_dados_producao():
    with aplicacao.app_context():
        print("--- INICIANDO CARGA DE USUÁRIOS DE PRODUÇÃO ---")

        # 1. CRIAR SETOR BASE
        setor_adm = Setor.query.filter_by(nome="Administração").first()
        if not setor_adm:
            setor_adm = Setor(nome="Administração", descricao="Diretoria e Gestão")
            db.session.add(setor_adm)
            db.session.flush() # Gera o ID

        # 2. CRIAR CARGO DE DONO (Acesso Total)
        cargo_dono = Cargo.query.filter_by(nome="Dono").first()
        if not cargo_dono:
            cargo_dono = Cargo(
                nome="Dono",
                setor_id=setor_adm.id,
                nivel_hierarquico=1, # Nível 1 libera tudo automaticamente
                descricao="Acesso total ao sistema ERP"
            )
            db.session.add(cargo_dono)
            db.session.flush()

        # 3. LISTA DAS CONTAS A SEREM CRIADAS
        # Obs: Os CPFs são fictícios para permitir a criação. Editem no RH depois.
        contas = [
            {
                "nome_completo": "Administrador Master",
                "cpf": "000.000.000-00",
                "login": "admin",
                "senha": "9rup019H@"
            },
            {
                "nome_completo": "Juliana",
                "cpf": "111.111.111-11",
                "login": "juliana",
                "senha": "123@mudar"
            },
            {
                "nome_completo": "Antonio",
                "cpf": "222.222.222-22",
                "login": "antonio",
                "senha": "123@mudar"
            }
        ]

        # 4. EXECUTAR A CRIAÇÃO
        for conta in contas:
            # 4.1 Criar Colaborador (Se não existir)
            colab = Colaborador.query.filter_by(cpf=conta["cpf"]).first()
            if not colab:
                colab = Colaborador(
                    nome_completo=conta["nome_completo"],
                    cpf=conta["cpf"],
                    data_admissao=date.today(),
                    cargo_id=cargo_dono.id,
                    tipo_contrato="Socio",
                    ativo=True
                )
                db.session.add(colab)
                db.session.flush()

            # 4.2 Criar Usuário (Se não existir)
            usuario = Usuario.query.filter_by(usuario=conta["login"]).first()
            if not usuario:
                usuario = Usuario(
                    usuario=conta["login"],
                    colaborador_id=colab.id,
                    ativo=True
                )
                usuario.definir_senha(conta["senha"])
                db.session.add(usuario)
                print(f"[+] Usuário criado com sucesso: {conta['login']}")
            else:
                # Se o usuário já existir, apenas reseta a senha para garantir
                usuario.definir_senha(conta["senha"])
                print(f"[*] Usuário '{conta['login']}' já existia. Senha resetada.")

        # Salva tudo no banco de uma vez
        db.session.commit()
        print("--- SUCESSO: BANCO DE PRODUÇÃO PREPARADO ---")

if __name__ == "__main__":
    criar_dados_producao()