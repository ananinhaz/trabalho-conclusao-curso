import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise SystemExit("ERRO: defina DATABASE_URL no .env antes de rodar este teste")

engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"}, pool_pre_ping=True)

with engine.connect() as conn:
    r = conn.execute(text("SELECT now()"))
    print("DB agora (UTC):", r.scalar())
