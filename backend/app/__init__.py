import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# extensões "padrão" (você já tem algo parecido)
db = SQLAlchemy()
migrate = Migrate()

# registraremos oauth via app.extensions.oauth.init_oauth(app)
# (você tem um módulo oauth em app/extensions/oauth.py com init_oauth)
def create_app():
    app = Flask(__name__, instance_relative_config=False)

    # --------------------------
    # CONFIGURAÇÕES DO SERVIDOR
    # --------------------------
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT
    app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "DEV_KEY_CHANGE_IN_PROD")
    app.config['JWT_TOKEN_LOCATION'] = ["headers"]
    app.config['JWT_HEADER_NAME'] = "Authorization"
    app.config['JWT_HEADER_TYPE'] = "Bearer"

    # FRONTEND EM PRODUÇÃO (default que você já usava)
    FRONT_HOME = os.environ.get(
        "FRONT_HOME",
        "https://trabalho-conclusao-curso-adoptme.vercel.app"
    )
    app.config["FRONT_HOME"] = FRONT_HOME

    # -------------------------
    # CORS (ESSENCIAL PARA JWT)
    # -------------------------
    CORS(app,
         resources={r"/api/*": {"origins": [FRONT_HOME]}},
         supports_credentials=False,
         expose_headers=["Authorization"]
    )

    # Inicializações das extensões
    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)

    # inicializa oauth (se presente)
    try:
        from .extensions.oauth import init_oauth
        init_oauth(app)
    except Exception as e:
        # apenas loga se não existir — não falha aqui
        print("⚠️ oauth init skipped:", e)

    # -------------------------
    # BLUEPRINTS
    # -------------------------
    # Importa *apenas* quando o app já está criado (evita import loops)
    try:
        from .controllers.auth_controller import auth_bp
        from .controllers.animal_controller import animais_bp
        from .controllers.usuario_controller import usuarios_bp
        # se tiver recommendation_controller, adoptor etc, importe aqui também
    except Exception as e:
        print("ERRO AO IMPORTAR CONTROLLERS:", e)
        raise

    # Registro dos blueprints
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(animais_bp, url_prefix="/api")
    app.register_blueprint(usuarios_bp, url_prefix="/api")

    # se quiser, registre rota de health
    try:
        from .health import bp as health_bp
        app.register_blueprint(health_bp, url_prefix="/")
    except Exception:
        pass

    return app
