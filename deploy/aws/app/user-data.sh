#!/usr/bin/env bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
SSM_PREFIX="${SSM_PREFIX:-/inframodel/prod/app}"
APP_DIR="/app"

apt-get update
apt-get install -y ca-certificates curl unzip awscli python3

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
cat >/etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

apt-get update
apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

systemctl enable --now docker
usermod -aG docker ubuntu || true

mkdir -p "$APP_DIR"
chown -R ubuntu:ubuntu "$APP_DIR"

ssm() {
  aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "$1" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text
}

ssm_optional() {
  local name="$1"
  local fallback="$2"
  local value

  if value="$(aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "$name" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text 2>/dev/null)"; then
    printf '%s\n' "$value"
  else
    printf '%s\n' "$fallback"
  fi
}

urlencode() {
  python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$1"
}

ARTIFACT_BUCKET="$(ssm "$SSM_PREFIX/artifact-bucket")"
aws s3 cp \
  "s3://$ARTIFACT_BUCKET/inframodel/prod/app/compose.yaml" \
  "$APP_DIR/compose.yaml"

ECR_REGISTRY="$(ssm "$SSM_PREFIX/ecr-registry")"
IMAGE_TAG="$(ssm "$SSM_PREFIX/image-tag")"
DB_WRITE_HOST="$(ssm "$SSM_PREFIX/db-write-host")"
DB_WRITE_PORT="$(ssm "$SSM_PREFIX/db-write-port")"
DB_READ_HOST="$(ssm "$SSM_PREFIX/db-read-host")"
DB_READ_PORT="$(ssm "$SSM_PREFIX/db-read-port")"
DB_NAME="$(ssm "$SSM_PREFIX/db-name")"
DB_USER="$(ssm "$SSM_PREFIX/db-user")"
DB_PASSWORD="$(ssm "$SSM_PREFIX/db-password")"
JWT_SECRET="$(ssm "$SSM_PREFIX/jwt-secret")"
ADMIN_PASSWORD="$(ssm "$SSM_PREFIX/admin-password")"
CORS_ORIGINS="$(ssm "$SSM_PREFIX/cors-origins")"
KMA_SERVICE_KEY="$(ssm "$SSM_PREFIX/kma-service-key")"
ACCOUNT_PROVIDER="$(ssm_optional "$SSM_PREFIX/account-provider" "local")"
COGNITO_REGION="$(ssm_optional "$SSM_PREFIX/cognito-region" "$AWS_REGION")"
COGNITO_USER_POOL_ID="$(ssm_optional "$SSM_PREFIX/cognito-user-pool-id" "")"
COGNITO_CLIENT_ID="$(ssm_optional "$SSM_PREFIX/cognito-client-id" "")"
DB_USER_URL="$(urlencode "$DB_USER")"
DB_PASSWORD_URL="$(urlencode "$DB_PASSWORD")"
DB_NAME_URL="$(urlencode "$DB_NAME")"

cat >"$APP_DIR/.env" <<EOF
ECR_REGISTRY=$ECR_REGISTRY
IMAGE_TAG=$IMAGE_TAG
WAS_PORT=8000

APP_NAME=Integrated Weather & Course WAS
ENVIRONMENT=production
DATA_MODE=database
WEATHER_MODE=database
WEATHER_STORAGE=database
WEATHER_DATABASE_BATCH_SIZE=1000
WEATHER_SNAPSHOT_RETENTION=3

WRITE_DATABASE_URL=mysql+asyncmy://$DB_USER_URL:$DB_PASSWORD_URL@$DB_WRITE_HOST:$DB_WRITE_PORT/$DB_NAME_URL
READ_DATABASE_URL=mysql+asyncmy://$DB_USER_URL:$DB_PASSWORD_URL@$DB_READ_HOST:$DB_READ_PORT/$DB_NAME_URL

REDIS_URL=redis://redis:6379/0
JWT_SECRET=$JWT_SECRET
ACCOUNT_PROVIDER=$ACCOUNT_PROVIDER
COGNITO_REGION=$COGNITO_REGION
COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID
COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$ADMIN_PASSWORD
CORS_ORIGINS=$CORS_ORIGINS
CORS_ORIGIN_REGEX=
COOKIE_SECURE=true

KMA_SERVICE_KEY=$KMA_SERVICE_KEY
KMA_COLLECTION_RETRIES=3
KMA_COLLECTION_RETRY_SECONDS=5
KMA_COLLECTION_CONCURRENCY=5
KMA_COURSE_LIMIT=0
EOF

chmod 0600 "$APP_DIR/.env"
chown ubuntu:ubuntu "$APP_DIR/.env"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

cd "$APP_DIR"
docker compose --env-file .env pull
docker compose --env-file .env up -d
docker compose ps
