import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tropucs')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"sslmode": "require"},
        "pool_pre_ping": True
    }

class DevelopmentConfig(Config):
    DEBUG = True
