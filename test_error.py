import sys
import traceback
from src.fabrica import criar_app
from src.modulos.autenticacao.modelos import Usuario
from src.extensoes import banco_de_dados as db

app = criar_app()

with app.test_client() as client:
    with app.app_context():
        user = Usuario.query.first()
        if user:
            print("Logando como:", user.email)
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
                
        try:
            response = client.get('/financeiro/')
            print("Status:", response.status_code)
            if response.status_code == 500:
                print(response.data.decode('utf-8'))
        except Exception as e:
            traceback.print_exc()
