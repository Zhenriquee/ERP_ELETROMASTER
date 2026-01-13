from functools import wraps
from flask import abort
from flask_login import current_user

def cargo_exigido(cargo_nome):
    """
    Decorator personalizado para verificar hierarquia.
    Uso: @cargo_exigido('gerente')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(401) # Não autorizado
            
            # Usa a lógica inteligente do modelo
            if not current_user.tem_permissao(cargo_nome):
                return abort(403) # Proibido (Logado, mas sem permissão)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator