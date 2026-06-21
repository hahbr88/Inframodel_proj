#!/usr/bin/env bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
SSM_PREFIX="${SSM_PREFIX:-/inframodel/prod/db}"
APP_DIR="/app"

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

ARTIFACT_BUCKET="$(ssm "$SSM_PREFIX/artifact-bucket")"
aws s3 cp \
  "s3://$ARTIFACT_BUCKET/inframodel/prod/db/compose.yaml" \
  "$APP_DIR/compose.yaml"

DB_BIND_IP="$(ssm "$SSM_PREFIX/db-bind-ip")"
MARIADB_DATABASE="$(ssm "$SSM_PREFIX/mariadb-database")"
MARIADB_USER="$(ssm "$SSM_PREFIX/mariadb-user")"
MARIADB_PASSWORD="$(ssm "$SSM_PREFIX/mariadb-password")"
MARIADB_ROOT_PASSWORD="$(ssm "$SSM_PREFIX/mariadb-root-password")"

cat >"$APP_DIR/.env" <<EOF
DB_BIND_IP=$DB_BIND_IP
MARIADB_DATABASE=$MARIADB_DATABASE
MARIADB_USER=$MARIADB_USER
MARIADB_PASSWORD=$MARIADB_PASSWORD
MARIADB_ROOT_PASSWORD=$MARIADB_ROOT_PASSWORD
EOF

chmod 0600 "$APP_DIR/.env"
chown ubuntu:ubuntu "$APP_DIR/.env"

cd "$APP_DIR"
docker compose --env-file .env up -d
docker compose ps
