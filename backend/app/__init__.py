from flask import Flask
from .config import Config, load_env
from .extensions.db import init_db_pool
from .api import register_blueprints
from .health import health_bp
from flask_cors import CORS


def create_app():
    load_env()                 # carrega .env
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:8000","http://localhost:8000"]}})
    init_db_pool(app)          # cria pool MySQL
    register_blueprints(app)   # registra controllers de recursos
    app.register_blueprint(health_bp)  

    @app.get("/")
    def home():
        return "Servidor Flask funcionando"
    return app
