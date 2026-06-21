#!/usr/bin/env bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
SSM_PREFIX="${SSM_PREFIX:-/inframodel/prod/db}"
APP_DIR="/app"

: "${GALERA_NODE_NAME:?Set GALERA_NODE_NAME in this DB node User Data}"
: "${GALERA_SERVER_ID:?Set GALERA_SERVER_ID in this DB node User Data}"
GALERA_READ_ONLY="${GALERA_READ_ONLY:-OFF}"
GALERA_BOOTSTRAP="${GALERA_BOOTSTRAP:-0}"

apt-get update
apt-get install -y ca-certificates curl unzip awscli

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

mkdir -p "$APP_DIR/config/vm" "$APP_DIR/secrets"
chown -R ubuntu:ubuntu "$APP_DIR"

ssm() {
  aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "$1" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text
}

imds() {
  local token
  token="$(curl -fsS -X PUT 'http://169.254.169.254/latest/api/token' \
    -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600')"
  curl -fsS -H "X-aws-ec2-metadata-token: $token" \
    "http://169.254.169.254/latest/meta-data/$1"
}

ARTIFACT_BUCKET="$(ssm "$SSM_PREFIX/artifact-bucket")"
aws s3 cp "s3://$ARTIFACT_BUCKET/inframodel/prod/db/compose.galera.yaml" "$APP_DIR/compose.yaml"
aws s3 cp "s3://$ARTIFACT_BUCKET/inframodel/prod/db/Dockerfile.galera" "$APP_DIR/Dockerfile.galera"
aws s3 cp "s3://$ARTIFACT_BUCKET/inframodel/prod/db/docker-entrypoint-galera.sh" "$APP_DIR/docker-entrypoint-galera.sh"
aws s3 cp "s3://$ARTIFACT_BUCKET/inframodel/prod/db/initdb-create-users.sh" "$APP_DIR/initdb-create-users.sh"
aws s3 cp "s3://$ARTIFACT_BUCKET/inframodel/prod/db/config/vm/60-galera-common.cnf" "$APP_DIR/config/vm/60-galera-common.cnf"

chmod 0755 "$APP_DIR/docker-entrypoint-galera.sh"
chmod 0644 "$APP_DIR/initdb-create-users.sh" "$APP_DIR/config/vm/60-galera-common.cnf"

MARIADB_DATABASE="$(ssm "$SSM_PREFIX/mariadb-database")"
MARIADB_USER="$(ssm "$SSM_PREFIX/mariadb-user")"
MARIADB_PASSWORD="$(ssm "$SSM_PREFIX/mariadb-password")"
MARIADB_ROOT_PASSWORD="$(ssm "$SSM_PREFIX/mariadb-root-password")"
MARIADB_SST_PASSWORD="$(ssm "$SSM_PREFIX/mariadb-sst-password")"
GALERA_CLUSTER_MEMBERS="$(ssm "$SSM_PREFIX/galera-cluster-members")"
GALERA_NODE_ADDRESS="${GALERA_NODE_ADDRESS:-$(imds local-ipv4)}"

cat >"$APP_DIR/.env" <<EOF
COMPOSE_PROJECT_NAME=galera-as-$GALERA_NODE_NAME
MARIADB_DATABASE=$MARIADB_DATABASE
MARIADB_USER=$MARIADB_USER
GALERA_CLUSTER_MEMBERS=$GALERA_CLUSTER_MEMBERS
GALERA_NODE_NAME=$GALERA_NODE_NAME
GALERA_SERVER_ID=$GALERA_SERVER_ID
GALERA_NODE_ADDRESS=$GALERA_NODE_ADDRESS
GALERA_READ_ONLY=$GALERA_READ_ONLY
GALERA_BOOTSTRAP=$GALERA_BOOTSTRAP
EOF

printf '%s' "$MARIADB_ROOT_PASSWORD" > "$APP_DIR/secrets/root_password.txt"
printf '%s' "$MARIADB_PASSWORD" > "$APP_DIR/secrets/app_password.txt"
printf '%s' "$MARIADB_SST_PASSWORD" > "$APP_DIR/secrets/sst_password.txt"
chmod 0600 "$APP_DIR/.env" "$APP_DIR"/secrets/*.txt
chown -R ubuntu:ubuntu "$APP_DIR"

cd "$APP_DIR"
docker compose --env-file .env build
docker compose --env-file .env up -d
docker compose ps
