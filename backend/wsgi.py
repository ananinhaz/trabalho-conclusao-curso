# backend/wsgi.py
import os
import sys

# Garante que a pasta `backend` (onde está o pacote `app`) esteja no sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # -> .../project/src/backend
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Agora podemos importar o pacote `app` (pasta backend/app)
# e criar a aplicação normalmente
try:
    from app import create_app
except Exception as e:
    # logs úteis em caso de erro de import — aparecerá nos logs do Render
    print("Error importing create_app:", e)
    raise

app = create_app()
