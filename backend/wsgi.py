# backend/wsgi.py
import os
import sys

# Caminho absoluto da pasta 'backend' (onde este arquivo está)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho do diretório pai (por exemplo: /opt/render/project/src)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# Garantir que tanto o backend quanto o project root estejam no sys.path
# assim o Python pode resolver imports como 'backend.app' independentemente
# de qual diretório o gunicorn for iniciado.
for p in (BACKEND_DIR, PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

# Agora importe o create_app a partir do pacote backend.app
try:
    # Tentamos importar como backend.app (mais explícito)
    from backend.app import create_app
except Exception as err:
    # Mensagem informativa para os logs do Render
    print("FALHA AO IMPORTAR create_app via backend.app:", err)
    # Tenta fallback: importar 'app' diretamente (antigo padrão)
    try:
        from app import create_app
    except Exception as err2:
        print("FALHA AO IMPORTAR create_app via app:", err2)
        raise

# Cria a app WSGI
app = create_app()
