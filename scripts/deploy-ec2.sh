#!/usr/bin/env bash
# Deploy em produção na EC2 — usa imagens do GHCR (build feito no GitHub Actions)
# Nunca executar: docker compose down -v | docker volume rm | docker compose build
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/trabalho-conclusao-curso}"
cd "$APP_DIR"

echo "==> Deploy AdoptMe em $APP_DIR"

# --- Proteger nginx.conf local da EC2 ---
NGINX_BACKUP="$(mktemp)"
trap 'STATUS=$?; rm -f "$NGINX_BACKUP"; [ $STATUS -ne 0 ] && echo "==> ERRO: deploy falhou na linha $LINENO"; exit $STATUS' EXIT
cp nginx/nginx.conf "$NGINX_BACKUP"

# --- Atualizar código ---
git fetch origin main
git checkout main
git pull --ff-only origin main

cp "$NGINX_BACKUP" nginx/nginx.conf

mkdir -p certbot/www certbot/conf

# --- Pull das imagens do GHCR (build foi feito no GitHub Actions) ---
docker pull ghcr.io/ananinhaz/adoptme-backend:latest
docker pull ghcr.io/ananinhaz/adoptme-frontend:latest

# --- Subir banco sem derrubar volume ---
docker compose -f docker-compose.prod.yml up -d db

# Aguardar Postgres saudável antes do backend
for i in $(seq 1 60); do
  if docker compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres -d adoptme >/dev/null 2>&1; then
    echo "==> Postgres pronto após $((i*2))s"
    break
  fi
  echo "==> Aguardando Postgres... ($i/60)"
  sleep 2
done

# --- Recriar backend e frontend ---
docker compose -f docker-compose.prod.yml up -d --no-deps --force-recreate backend
docker compose -f docker-compose.prod.yml up -d --no-deps --force-recreate frontend

# --- Nginx: recriar só se nginx.conf mudou ---
HASH_FILE="$APP_DIR/.nginx.conf.deploy-hash"
NEW_HASH="$(md5sum nginx/nginx.conf | awk '{print $1}')"
OLD_HASH=""
if [ -f "$HASH_FILE" ]; then
  OLD_HASH="$(cat "$HASH_FILE")"
fi

if [ "$NEW_HASH" != "$OLD_HASH" ]; then
  echo "==> nginx.conf alterado — recriando tcc_nginx"
  docker compose -f docker-compose.prod.yml up -d --no-deps --force-recreate nginx
  echo "$NEW_HASH" > "$HASH_FILE"
else
  echo "==> nginx.conf inalterado — mantendo tcc_nginx"
  docker compose -f docker-compose.prod.yml up -d nginx
fi

# Limpar imagens órfãs (não remove volumes)
docker image prune -f

echo "==> Deploy concluído"
docker compose -f docker-compose.prod.yml ps