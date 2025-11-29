import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
# IMPORTANTE: Mantenha o ProxyFix
from werkzeug.middleware.proxy_fix import ProxyFix

from .health import health_bp

def create_app():
    load_dotenv()

    app = Flask(__name__)
    
    # CRÍTICO: Informa ao Flask que está atrás de um proxy HTTPS (Render).
    # Essencial para que o SESSION_COOKIE_SECURE=True funcione.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    # FRONT_HOME configurado (frontend) — usado no CORS e para decidir cookie secure
    frontend_origin = os.getenv("FRONT_HOME", "http://localhost:5173").rstrip('/')

    # Detecção de ambiente segura: considera HTTPS (Produção) e ambiente local.
    is_local_frontend = frontend_origin.startswith("http://localhost") or frontend_origin.startswith("http://127.0.0.1")
    
    # 💡 LÓGICA REFORÇADA: Força as flags de segurança se a URL for HTTPS ou se não for ambiente local
    is_secure_needed = frontend_origin.startswith("https://") or (not is_local_frontend)

    # Em ambiente seguro (HTTPS/Produção), usamos SameSite=None e Secure=True
    session_cookie_secure = is_secure_needed
    session_cookie_samesite = "None" if is_secure_needed else "Lax"

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret"),
        # CONFIGURAÇÕES FINAIS DE COOKIE (CRÍTICAS PARA CORS/PRODUÇÃO)
        SESSION_COOKIE_SAMESITE=session_cookie_samesite,
        SESSION_COOKIE_SECURE=session_cookie_secure,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_PERMANENT=False,

        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"sslmode": "require"}, "pool_pre_ping": True}
    )

    # allowed origins: locais + frontend production (da env)
    allowed_origins = [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        frontend_origin,
    ]

    # CORS: permita credenciais e somente o frontend
    CORS(
        app,
        supports_credentials=True, # ESSENCIAL para enviar cookies de sessão
        resources={r"/*": {"origins": allowed_origins}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type"],
    )

    # extensões
    from .extensions.oauth import init_oauth
    init_oauth(app)

    from .extensions.db import init_db
    init_db(app)

    # blueprints
    from .controllers.auth_controller import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .api import register_blueprints
    register_blueprints(app)

    # Registro do Blueprint de saúde
    app.register_blueprint(health_bp)

    @app.get("/")
    def index():
        return "API AdoptMe OK"

    return app

app = create_app()