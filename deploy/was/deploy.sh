#!/usr/bin/env bash
set -euo pipefail

WAS_IP="${WAS_IP:-192.168.100.20}"
DB_IP="${DB_IP:-192.168.100.30}"
WEB_IP="${WEB_IP:-192.168.100.10}"

DB_NAME="${DB_NAME:-integrated}"
DB_USER="${DB_USER:-app}"
DB_PASSWORD="${DB_PASSWORD:-}"
JWT_SECRET="${JWT_SECRET:-}"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"
KMA_SERVICE_KEY="${KMA_SERVICE_KEY:-}"
KMA_COLLECTION_CONCURRENCY="${KMA_COLLECTION_CONCURRENCY:-10}"
KMA_COURSE_LIMIT="${KMA_COURSE_LIMIT:-0}"
RESET_COMPOSE="${RESET_COMPOSE:-no}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

fail() {
  echo "오류: $*" >&2
  exit 1
}

[[ -f $REPO_ROOT/apps/integrated-was/Dockerfile ]] \
  || fail "apps/integrated-was 소스를 찾지 못했습니다."
command -v docker >/dev/null || fail "Docker가 설치되어 있지 않습니다."
ip -4 -o address show | awk '{print $4}' | cut -d/ -f1 \
  | grep -Fxq "$WAS_IP" \
  || fail "$WAS_IP가 이 VM에 설정되어 있지 않습니다."
[[ $DB_PASSWORD =~ ^[A-Za-z0-9._~-]+$ ]] \
  || fail "DB_PASSWORD를 영문, 숫자, 점, 밑줄, 물결표, 하이픈으로 지정하세요."
[[ ${#JWT_SECRET} -ge 32 && $JWT_SECRET =~ ^[A-Za-z0-9._~-]+$ ]] \
  || fail "JWT_SECRET을 32자 이상의 안전한 문자열로 지정하세요."
[[ $ADMIN_PASSWORD =~ ^[A-Za-z0-9._~-]+$ ]] \
  || fail "ADMIN_PASSWORD를 지정하세요."

cat >"$SCRIPT_DIR/.env" <<EOF
WAS_BIND_IP=$WAS_IP
APP_NAME=Integrated Weather & Course WAS
ENVIRONMENT=production
DATA_MODE=database
WEATHER_MODE=database
WEATHER_STORAGE=database
WEATHER_DATABASE_BATCH_SIZE=1000
WEATHER_SNAPSHOT_RETENTION=3
WRITE_DATABASE_URL=mysql+asyncmy://$DB_USER:$DB_PASSWORD@$DB_IP:3306/$DB_NAME
READ_DATABASE_URL=mysql+asyncmy://$DB_USER:$DB_PASSWORD@$DB_IP:3306/$DB_NAME
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=$JWT_SECRET
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
CORS_ORIGINS=http://$WEB_IP
CORS_ORIGIN_REGEX=
COOKIE_SECURE=false
KMA_SERVICE_KEY=$KMA_SERVICE_KEY
KMA_COLLECTION_RETRIES=3
KMA_COLLECTION_RETRY_SECONDS=5
KMA_COLLECTION_CONCURRENCY=$KMA_COLLECTION_CONCURRENCY
KMA_COURSE_LIMIT=$KMA_COURSE_LIMIT
EOF
chmod 600 "$SCRIPT_DIR/.env"

cd "$SCRIPT_DIR"
docker compose config --quiet

if [[ $RESET_COMPOSE == yes ]]; then
  docker compose down
fi

docker compose up -d --build
docker compose ps

if [[ -z $KMA_SERVICE_KEY ]]; then
  echo "경고: KMA_SERVICE_KEY가 없어 날씨 수집기는 아직 실행할 수 없습니다."
fi
