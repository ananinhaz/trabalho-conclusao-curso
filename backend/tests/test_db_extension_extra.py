import pytest

import app.extensions.db as db_mod


class DummyRawConn:
    def __init__(self):
        self.closed = False
        self.committed = 0
        self.rolled_back = 0
        self.autocommit = True

    def cursor(self, *args, **kwargs):
        class Cur:
            def execute(self, *_a, **_k):
                return None

            def fetchone(self):
                return (1,)

            def close(self):
                return None

        return Cur()

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1

    def close(self):
        self.closed = True


class MysqlConn(DummyRawConn):
    def __init__(self):
        super().__init__()
        self.reconnect_called = 0

    def is_connected(self):
        return False

    def reconnect(self, attempts=1, delay=0):
        self.reconnect_called += 1


class DummyPool:
    def __init__(self, conn):
        self._conn = conn
        self.put_called = 0

    def getconn(self):
        return self._conn

    def putconn(self, _conn):
        self.put_called += 1


class DummyMysqlPool:
    def __init__(self, conn):
        self._conn = conn

    def get_connection(self):
        return self._conn


def test_sqlite_wrapper_execute_and_fetch(tmp_path):
    db_path = tmp_path / "x.db"
    conn = db_mod._SQLiteConnectionWrapper(str(db_path))
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, nome TEXT)")
        cur.executemany("INSERT INTO t(nome) VALUES (%s)", [("a",), ("b",)])
    conn.commit()

    with conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT id, nome FROM t WHERE nome=%s", ("a",))
        one = cur.fetchone()
        assert one["nome"] == "a"
        cur.execute("SELECT id, nome FROM t")
        rows = cur.fetchall()
        assert len(rows) == 2
        _ = cur.lastrowid
        _ = cur.rowcount
    conn.close()


def test_init_db_sqlite_and_get_conn(monkeypatch, tmp_path):
    db_path = tmp_path / "sqlite_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    prev = (db_mod._using_sqlite, db_mod._using_postgres, db_mod._sqlite_path)
    try:
        db_mod.init_db()
        assert db_mod.using_sqlite() is True

        conn = db_mod.get_conn()
        assert conn is not None
        conn.close()
    finally:
        db_mod._using_sqlite, db_mod._using_postgres, db_mod._sqlite_path = prev


def test_init_db_rejects_postgres_in_tests(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://example")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "x")
    with pytest.raises(RuntimeError):
        db_mod.init_db()


def test_init_db_postgres_path(monkeypatch):
    raw = DummyRawConn()
    pool = DummyPool(raw)

    monkeypatch.setenv("DATABASE_URL", "postgres://example")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(db_mod, "_psycopg2", object())
    monkeypatch.setattr(db_mod, "ThreadedConnectionPool", lambda *_a, **_k: pool)

    prev = (db_mod._using_sqlite, db_mod._using_postgres, db_mod._sqlite_path, db_mod._pg_pool)
    try:
        db_mod.init_db()
        assert db_mod._using_postgres is True
        assert pool.put_called == 1
    finally:
        db_mod._using_sqlite, db_mod._using_postgres, db_mod._sqlite_path, db_mod._pg_pool = prev


def test_init_db_mysql_path(monkeypatch):
    raw = DummyRawConn()

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(db_mod, "_MYSQL_AVAILABLE", True)
    monkeypatch.setattr(db_mod, "mysql_connect", lambda **_k: raw)
    monkeypatch.setattr(db_mod, "MySQLConnectionPool", lambda **_k: "POOL")

    prev = (db_mod._using_sqlite, db_mod._using_postgres, db_mod._mysql_pool)
    try:
        db_mod.init_db()
        assert db_mod._mysql_pool == "POOL"
    finally:
        db_mod._using_sqlite, db_mod._using_postgres, db_mod._mysql_pool = prev


def test_get_raw_conn_errors_when_no_pool(monkeypatch):
    monkeypatch.setattr(db_mod, "_using_sqlite", False)
    monkeypatch.setattr(db_mod, "_using_postgres", False)
    monkeypatch.setattr(db_mod, "_mysql_pool", None)
    with pytest.raises(RuntimeError):
        db_mod._get_raw_conn()


def test_get_raw_conn_postgres_pool(monkeypatch):
    raw = DummyRawConn()

    class Pool:
        def getconn(self):
            return raw

    monkeypatch.setattr(db_mod, "_using_sqlite", False)
    monkeypatch.setattr(db_mod, "_using_postgres", True)
    monkeypatch.setattr(db_mod, "_pg_pool", Pool())

    conn = db_mod._get_raw_conn()
    assert conn is raw
    assert conn.autocommit is False


def test_get_raw_conn_mysql_reconnect(monkeypatch):
    conn = MysqlConn()
    monkeypatch.setattr(db_mod, "_using_sqlite", False)
    monkeypatch.setattr(db_mod, "_using_postgres", False)
    monkeypatch.setattr(db_mod, "_mysql_pool", DummyMysqlPool(conn))

    got = db_mod._get_raw_conn()
    assert got is conn
    assert conn.reconnect_called >= 1


def test_connproxy_cursor_modes(monkeypatch):
    raw = DummyRawConn()

    monkeypatch.setattr(db_mod, "_using_postgres", False)
    proxy = db_mod.ConnProxy(raw)
    cur = proxy.cursor(dictionary=True)
    assert cur is not None

    class FakeExtras:
        RealDictCursor = object

    monkeypatch.setattr(db_mod, "_using_postgres", True)
    monkeypatch.setattr(db_mod, "_pg_extras", FakeExtras)
    cur2 = proxy.cursor(dictionary=True)
    assert cur2 is not None


def test_connproxy_close_paths(monkeypatch):
    raw = DummyRawConn()
    pool = DummyPool(raw)

    monkeypatch.setattr(db_mod, "_using_postgres", True)
    monkeypatch.setattr(db_mod, "_pg_pool", pool)
    db_mod.ConnProxy(raw).close()
    assert pool.put_called == 1

    monkeypatch.setattr(db_mod, "_using_postgres", False)
    db_mod.ConnProxy(raw).close()
    assert raw.closed is True


def test_db_context_manager_commit_and_rollback(monkeypatch):
    raw = DummyRawConn()
    monkeypatch.setattr(db_mod, "_get_raw_conn", lambda: raw)
    monkeypatch.setattr(db_mod, "_using_postgres", False)

    with db_mod.db() as conn:
        conn.cursor(dictionary=True)

    assert raw.committed == 1

    raw2 = DummyRawConn()
    monkeypatch.setattr(db_mod, "_get_raw_conn", lambda: raw2)

    with pytest.raises(ValueError):
        with db_mod.db():
            raise ValueError("boom")

    assert raw2.rolled_back == 1
