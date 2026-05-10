import os

import app as app_pkg


def test_normalize_database_url_variants():
    assert app_pkg._normalize_database_url("sqlite:///x.db") == "sqlite:///x.db"

    pg = app_pkg._normalize_database_url("postgres://u:p@h/db")
    assert pg.startswith("postgresql+psycopg2://")
    assert "sslmode=require" in pg



def test_create_app_root_and_health(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "s")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "j")
    app = app_pkg.create_app()
    c = app.test_client()

    assert c.get("/").status_code == 200
    assert c.get("/health").status_code == 200
