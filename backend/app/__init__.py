import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
# IMPORTANTE: Mantenha o ProxyFix
from werkzeug.middleware.proxy_fix import ProxyFix
# 💡 NOVO: Importar JWTManager
from flask_jwt_extended import JWTManager 

from .health import health_bp

def create_app():
    load_dotenv()

    app = Flask(__name__)
    
    # CRÍTICO: Informa ao Flask que está atrás de um proxy HTTPS (Render).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    # FRONT_HOME configurado (frontend) — usado no CORS
    frontend_origin = os.getenv("FRONT_HOME", "http://localhost:5173").rstrip('/')

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret"),
        
        # ❌ REMOVIDAS: todas as configurações SESSION_COOKIE_..., SESSION_PERMANENT, etc.
        
        # 💡 NOVO: Configuração JWT
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "uma-chave-secreta-forte-para-jwt"),
        # Token expira em 30 minutos (sugestão segura)
        JWT_ACCESS_TOKEN_EXPIRES=1800, 

        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"sslmode": "require"}, "pool_pre_ping": True}
    )

    # 💡 NOVO: Inicializar o JWTManager
    jwt = JWTManager(app)

    # allowed origins: locais + frontend production (da env)
    allowed_origins = [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        frontend_origin,
    ]

    # CORS: Manter supports_credentials=True, mas focar em 'Authorization' nos headers
    CORS(
        app,
        supports_credentials=True, 
        resources={r"/*": {"origins": allowed_origins}},
        allow_headers=["Content-Type", "Authorization"], # Authorization é essencial para o JWT
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