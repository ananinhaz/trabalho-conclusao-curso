import os
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]  
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app

@pytest.fixture
def app():
    # evita tocar variáveis de produção
    os.environ["FLASK_ENV"] = "testing"
    
    app = create_app()

    # Desativa a exigência de HTTPS para cookies
    app.config['SESSION_COOKIE_SECURE'] = False
    # Define uma chave secreta, necessária para o Flask assinar o cookie de sessão
    app.config['SECRET_KEY'] = 'test-secret-key' 
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()