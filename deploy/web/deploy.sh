#!/usr/bin/env bash
set -euo pipefail

WAS_IP="${WAS_IP:-192.168.100.20}"
WAS_PORT="${WAS_PORT:-8000}"
RESET_COMPOSE="${RESET_COMPOSE:-no}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

[[ -f $REPO_ROOT/apps/service-web/package.json ]] \
  || { echo "apps/service-web 소스를 찾지 못했습니다." >&2; exit 1; }
[[ -f $REPO_ROOT/apps/admin-web/package.json ]] \
  || { echo "apps/admin-web 소스를 찾지 못했습니다." >&2; exit 1; }
command -v docker >/dev/null || { echo "Docker가 설치되어 있지 않습니다." >&2; exit 1; }

cat >"$SCRIPT_DIR/.env" <<EOF
WAS_HOST=$WAS_IP
WAS_PORT=$WAS_PORT
EOF
chmod 600 "$SCRIPT_DIR/.env"

cd "$SCRIPT_DIR"
docker compose config --quiet

if [[ $RESET_COMPOSE == yes ]]; then
  docker compose down
fi

docker compose up -d --build
docker compose ps

echo "사용자 웹: http://$(hostname -I | awk '{print $1}')/"
echo "관리자 웹: http://$(hostname -I | awk '{print $1}')/admin/"
