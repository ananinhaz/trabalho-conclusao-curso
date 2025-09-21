from mysql.connector import pooling

_pool = None

def init_db_pool(app):
    global _pool
    _pool = pooling.MySQLConnectionPool(
        pool_name="adoptme_pool",
        pool_size=app.config["DB_POOL_SIZE"],
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASS"],
        database=app.config["DB_NAME"],
        connection_timeout=app.config["DB_TIMEOUT"],
        use_pure=True
    )

def get_conn():
    if _pool is None:
        raise RuntimeError("DB pool não inicializado")
    return _pool.get_connection()
