import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
# IMPORTANTE: Mantenha o ProxyFix
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import JWTManager # NOVO IMPORT

from .health import health_bp

def create_app():
    load_dotenv()

    app = Flask(__name__)
    
    # CRÍTICO: Informa ao Flask que está atrás de um proxy HTTPS (Render).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    frontend_origin = os.getenv("FRONT_HOME", "http://localhost:5173").rstrip('/')
    
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret"),
        
        # 💡 Configuração LIMPA para JWT
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "437cb951bcb6b59bb6368b0609ecba51dd45a6f00ec22a73c71bde25f60388f0"),
        JWT_ACCESS_TOKEN_EXPIRES=1800, # 30 minutos
        
        # REMOVIDOS os configs de SESSION_COOKIE_... e PERMANENT_SESSION_LIFETIME

        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"sslmode": "require"}, "pool_pre_ping": True}
    )

    # 💡 Inicializar o JWTManager
    jwt = JWTManager(app)

    # allowed origins: locais + frontend production (da env)
    allowed_origins = [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        frontend_origin,
    ]

    # CORS: Não suporta credenciais (cookies), foca nos headers (JWT)
    CORS(
        app,
        supports_credentials=False, # MUDANÇA: Foco em Headers, não cookies
        resources={r"/*": {"origins": allowed_origins}},
        allow_headers=["Content-Type", "Authorization"], # Authorization é essencial
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type"],
    )

    # extensões
    from .extensions.oauth import init_oauth
    init_oauth(app)

    from .extensions.db import init_db
    init_db(app)

    # blueprints
    from .routes import auth, perfil_adotante, animais
    app.register_blueprint(auth.bp)
    app.register_blueprint(perfil_adotante.bp)
    app.register_blueprint(animais.bp)
    app.register_blueprint(health_bp)

    return app