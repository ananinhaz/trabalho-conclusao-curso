"""Constantes compartilhadas (SQL, mensagens de API, DSN)."""

ERR_UNAUTHENTICATED = "unauthenticated"

# DSN PostgreSQL (Docker Compose / testes locais)
DOCKER_POSTGRES_DSN = "postgresql://postgres:postgres@db:5432/adoptme"

# Esquemas de URL PostgreSQL
POSTGRES_URL_SCHEME = "postgres://"
POSTGRESQL_URL_SCHEME = "postgresql://"
POSTGRESQL_PSYCOPG2_SCHEME = "postgresql+psycopg2://"

# --- SQL: animais ---
SQL_SELECT_DONOR_BY_ANIMAL_ID = "SELECT doador_id FROM animais WHERE id=%s"
SQL_SELECT_ANIMAL_BY_ID = "SELECT * FROM animais WHERE id=%s"
SQL_DELETE_ANIMAL_BY_ID = "DELETE FROM animais WHERE id=%s"

SQL_SELECT_ANIMAL_ROW = """
                SELECT id, nome, especie, raca, idade, porte, descricao,
                       cidade, photo_url, donor_name, donor_whatsapp,
                       doador_id, criado_em AS created_at,
                       energia, bom_com_criancas, adotado_em
                  FROM animais"""

SQL_SELECT_ANIMAL_ROW_NO_OWNER = """
                SELECT id, nome, especie, raca, idade, porte, descricao,
                       cidade, photo_url, donor_name, donor_whatsapp,
                       criado_em AS created_at,
                       energia, bom_com_criancas, adotado_em
                  FROM animais"""

SQL_INSERT_ANIMAL = """
                    INSERT INTO animais
                        (doador_id, nome, especie, raca, idade, porte,
                         descricao, cidade, photo_url, donor_name, donor_whatsapp,
                         energia, bom_com_criancas)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

SQL_INSERT_PERFIL_VALUES = """
                    INSERT INTO perfil_adotante
                        (usuario_id, tipo_moradia, tem_criancas,
                         tempo_disponivel_horas_semana, estilo_vida)
                    VALUES (%s, %s, %s, %s, %s)"""

# --- SQL: usuarios ---
SQL_USER_BY_ID = "SELECT id, nome, email, avatar_url FROM usuarios WHERE id=%s"
SQL_USER_ID_BY_EMAIL = "SELECT id FROM usuarios WHERE email=%s"
SQL_USER_ID_BY_GOOGLE_SUB = "SELECT id FROM usuarios WHERE google_sub=%s"
SQL_USER_LOGIN_BY_EMAIL = "SELECT id, password_hash FROM usuarios WHERE email=%s"
SQL_INSERT_USER_PASSWORD = "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s)"
SQL_INSERT_USER_PASSWORD_RETURNING = (
    "INSERT INTO usuarios (nome,email,password_hash) VALUES (%s,%s,%s) RETURNING id"
)
SQL_INSERT_USER_GOOGLE = (
    "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s)"
)
SQL_INSERT_USER_GOOGLE_RETURNING = (
    "INSERT INTO usuarios (nome,email,google_sub,avatar_url) VALUES (%s,%s,%s,%s) RETURNING id"
)
