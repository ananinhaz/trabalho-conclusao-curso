import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Importação do Blueprint de saúde
from .health import health_bp

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret"),
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        SESSION_PERMANENT=False,
        SESSION_COOKIE_DOMAIN="127.0.0.1",
    )
    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": [
            "http://127.0.0.1:8080",
            "http://localhost:8080",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type"],
    )

    @app.before_request
    def _preflight():
        if request.method == "OPTIONS":
            return app.make_response(("", 200))

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

    # NOVO: Registro do Blueprint de saúde
    # Isso adiciona as rotas /db-health e /tables
    app.register_blueprint(health_bp) 

    # REMOVIDO: Rota /health simples. 
    # Ela estava em conflito com o seu app/health.py e impedindo a cobertura.
    # A rota /db-health agora é usada para checar a saúde do DB.

    @app.get("/")
    def index():
        return "API AdoptMe OK"

    return app