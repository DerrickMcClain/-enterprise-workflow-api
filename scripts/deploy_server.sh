#!/usr/bin/env sh
# On the VPS, from repo root, after .env exists:
#   export DEPLOY_BRANCH=main
#   sh scripts/deploy_server.sh
set -e
cd "$(dirname "$0")/.."
BRANCH="${DEPLOY_BRANCH:-main}"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker compose -f docker-compose.prod.yml --env-file .env ps
