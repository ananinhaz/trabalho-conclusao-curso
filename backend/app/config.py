import os
from dotenv import load_dotenv as _load_dotenv

def load_env():
    # chama isso no create_app; não explode se .env não existir
    _load_dotenv(override=False)

class Config:
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "pyuser")
    DB_PASS = os.getenv("DB_PASS", "ana123")
    DB_NAME = os.getenv("DB_NAME", "adoptme")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "5"))
    # adicione aqui configs futuras (JWT_SECRET, GOOGLE_CLIENT_ID, etc.)
