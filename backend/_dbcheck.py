import os, sys
import mysql.connector as mc
from dotenv import load_dotenv

load_dotenv()
cfg = dict(
    host=os.getenv('DB_HOST','127.0.0.1'),
    port=int(os.getenv('DB_PORT','3306')),
    user=os.getenv('DB_USER','root'),
    password=os.getenv('DB_PASSWORD',''),
    database=os.getenv('DB_NAME','adoptme'),
    connection_timeout=5,
    allow_public_key_retrieval=True,  
)
print('CFG=', cfg)
try:
    conn = mc.connect(**cfg)
    print('Connected=', conn.is_connected())
    cur = conn.cursor()
    cur.execute('SELECT 1')
    print('SELECT 1 ->', cur.fetchone())
    cur.close(); conn.close()
except Exception as e:
    print('ERR:', type(e).__name__, e)
    sys.exit(1)
