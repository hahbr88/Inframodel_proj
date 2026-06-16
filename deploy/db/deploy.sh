#!/usr/bin/env bash
set -euo pipefail

DB_IP="${DB_IP:-192.168.100.30}"
DB_NAME="${DB_NAME:-integrated}"
DB_USER="${DB_USER:-app}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-}"
RESET_COMPOSE="${RESET_COMPOSE:-no}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

fail() {
  echo "오류: $*" >&2
  exit 1
}

command -v docker >/dev/null || fail "Docker가 설치되어 있지 않습니다."
ip -4 -o address show | awk '{print $4}' | cut -d/ -f1 \
  | grep -Fxq "$DB_IP" \
  || fail "$DB_IP가 이 VM에 설정되어 있지 않습니다."
[[ $DB_PASSWORD =~ ^[A-Za-z0-9._~-]+$ ]] \
  || fail "DB_PASSWORD를 영문, 숫자, 점, 밑줄, 물결표, 하이픈으로 지정하세요."
[[ $DB_ROOT_PASSWORD =~ ^[A-Za-z0-9._~-]+$ ]] \
  || fail "DB_ROOT_PASSWORD를 지정하세요."

cat >"$SCRIPT_DIR/.env" <<EOF
DB_BIND_IP=$DB_IP
MARIADB_DATABASE=$DB_NAME
MARIADB_USER=$DB_USER
MARIADB_PASSWORD=$DB_PASSWORD
MARIADB_ROOT_PASSWORD=$DB_ROOT_PASSWORD
EOF
chmod 600 "$SCRIPT_DIR/.env"

cd "$SCRIPT_DIR"
docker compose config --quiet

if [[ $RESET_COMPOSE == yes ]]; then
  docker compose down
fi

docker compose pull
docker compose up -d
docker compose ps
