#!/usr/bin/env bash
set -euo pipefail

HTTP_BIND_IP="${HTTP_BIND_IP:-0.0.0.0}"
HTTP_PORT="${HTTP_PORT:-80}"
DB_HOST="${DB_HOST:-10.250.10.10}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-integrated}"
DB_USER="${DB_USER:-app}"
DB_PASSWORD="${DB_PASSWORD:-1234}"
JWT_SECRET="${JWT_SECRET:-my_super_secret_key_string_32chars_long}"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-1234}"
PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-http://tripkey.shop}"
CORS_ORIGINS="${CORS_ORIGINS:-http://tripkey.shop}"
CORS_ORIGIN_REGEX="${CORS_ORIGIN_REGEX:-}"
COOKIE_SECURE="${COOKIE_SECURE:-false}"
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

first_host_ip() {
  hostname -I | awk '{print $1}'
}

[[ -f $REPO_ROOT/apps/service-web/package.json ]] \
  || fail "apps/service-web 소스를 찾지 못했습니다."
[[ -f $REPO_ROOT/apps/admin-web/package.json ]] \
  || fail "apps/admin-web 소스를 찾지 못했습니다."
[[ -f $REPO_ROOT/apps/integrated-was/Dockerfile ]] \
  || fail "apps/integrated-was 소스를 찾지 못했습니다."
command -v docker >/dev/null || fail "Docker가 설치되어 있지 않습니다."

[[ $DB_PASSWORD =~ ^[-A-Za-z0-9._~-]+$ ]] \
  || fail "DB_PASSWORD를 영문, 숫자, 점, 밑줄, 물결표, 하이픈으로 지정하세요."
[[ ${#JWT_SECRET} -ge 32 && $JWT_SECRET =~ ^[A-Za-z0-9._~-]+$ ]] \
  || fail "JWT_SECRET을 32자 이상의 안전한 문자열로 지정하세요."
[[ $ADMIN_PASSWORD =~ ^[A-Za-z0-9._~-]+$ ]] \
  || fail "ADMIN_PASSWORD를 지정하세요."

if [[ -z $PUBLIC_ORIGIN ]]; then
  PUBLIC_ORIGIN="http://$(first_host_ip)"
fi
if [[ -z $CORS_ORIGINS ]]; then
  CORS_ORIGINS="$PUBLIC_ORIGIN"
fi

cat >"$SCRIPT_DIR/.env" <<EOF
HTTP_BIND_IP=$HTTP_BIND_IP
HTTP_PORT=$HTTP_PORT
APP_NAME=Integrated Weather & Course WAS
ENVIRONMENT=production
DATA_MODE=database
WEATHER_MODE=database
WEATHER_STORAGE=database
WEATHER_DATABASE_BATCH_SIZE=1000
WEATHER_SNAPSHOT_RETENTION=3
WRITE_DATABASE_URL=mysql+asyncmy://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
READ_DATABASE_URL=mysql+asyncmy://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=$JWT_SECRET
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
CORS_ORIGINS=$CORS_ORIGINS
CORS_ORIGIN_REGEX=$CORS_ORIGIN_REGEX
COOKIE_SECURE=$COOKIE_SECURE
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

docker compose up -d --build --force-recreate
docker compose ps

echo "사용자 웹: $PUBLIC_ORIGIN/"
echo "관리자 웹: $PUBLIC_ORIGIN/admin/"
echo "API 프록시: $PUBLIC_ORIGIN/api/"

if [[ -z $KMA_SERVICE_KEY ]]; then
  echo "경고: KMA_SERVICE_KEY가 없어 날씨 수집기는 아직 실행할 수 없습니다."
fi
