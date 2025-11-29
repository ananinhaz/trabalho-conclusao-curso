import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
# IMPORTANTE: Mantenha o ProxyFix para ambientes com proxy (como o Render)
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import JWTManager

from .health import health_bp

def create_app():
    load_dotenv()

    app = Flask(__name__)
    
    # CRÍTICO: Informa ao Flask que está atrás de um proxy HTTPS (Render).
    # Essencial para que o SESSION_COOKIE_SECURE=True e os JWT Cookies funcionem.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    # JWT Configuração
    # SECRET_KEY pode ser a mesma variável de ambiente
    app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY", "SUA_CHAVE_SECRETA_JWT_AQUI")
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    # CRÍTICO: Não aceita o token no JSON, apenas no cookie
    # O cookie só é seguro se a URL do FRONT_HOME começar com https:// (ambiente prod)
    app.config["JWT_COOKIE_SECURE"] = os.getenv("FRONT_HOME", "").startswith("https://") or (not os.getenv("FRONT_HOME", "").startswith(("http://localhost", "http://127.0.0.1")))
    app.config["JWT_COOKIE_SAMESITE"] = "Lax" # 'Lax' é bom para segurança e usabilidade (CSRF)
    app.config["JWT_COOKIE_HTTPONLY"] = True # IMPEDE JAVASCRIPT DE LER O COOKIE (SEGURANÇA)
    app.config["JWT_COOKIE_PATH"] = "/"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600 * 24 * 7 # 7 dias

    # Configurações gerais
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "SUA_CHAVE_SECRETA_AQUI"),
        # Configuração padrão, embora não usemos session padrão com JWT
        SESSION_PERMANENT=False,

        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"sslmode": "require"}, "pool_pre_ping": True}
    )

    # Inicializa JWTManager
    jwt = JWTManager(app)

    # FRONT_HOME configurado (frontend) — usado no CORS
    frontend_origin = os.getenv("FRONT_HOME", "http://localhost:5173").rstrip('/')
    
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
        supports_credentials=True, # ESSENCIAL para enviar cookies
        resources={r"/*": {"origins": allowed_origins}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type", "Set-Cookie"],
    )

    # extensões
    from .extensions.oauth import init_oauth
    init_oauth(app)

    from .extensions.db import init_db
    init_db(app)
    
    # 🚨 CORREÇÃO DE IMPORTAÇÃO PARA SUA ESTRUTURA: Importa os blueprints diretamente da pasta 'app/'
    from .auth_controller import bp as auth_bp 
    from .api import bp_api 

    # Registro de Blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    # Assumimos que 'bp_api' tem as rotas de animais e perfil_adotante
    app.register_blueprint(bp_api, url_prefix='/')

    # Handler para erro 401 (Não Autorizado) no JWT
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        # Redireciona para o login se não estiver autorizado
        return jsonify(ok=False, error="Sessão expirada ou não autorizada. Por favor, faça login novamente."), 401

    @jwt.invalid_token_loader
    @jwt.expired_token_loader
    @jwt.revoked_token_loader
    @jwt.token_verification_error_loader
    def security_token_callback(callback):
        # Retorna erro no JSON, o frontend saberá redirecionar
        return jsonify(ok=False, error="Token inválido. Por favor, faça login novamente."), 401


    return app