#!/usr/bin/env bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
SSM_PREFIX="${SSM_PREFIX:-/inframodel/prod/db}"
APP_DIR="/app"
HAPROXY_NODE_NAME="${HAPROXY_NODE_NAME:-haproxy}"

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

mkdir -p "$APP_DIR/haproxy"
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
aws s3 cp "s3://$ARTIFACT_BUCKET/inframodel/prod/db/compose.haproxy.yaml" "$APP_DIR/compose.yaml"

DB1_HOST="$(ssm "$SSM_PREFIX/db1-host")"
DB2_HOST="$(ssm "$SSM_PREFIX/db2-host")"
DB3_HOST="$(ssm "$SSM_PREFIX/db3-host")"

cat >"$APP_DIR/.env" <<EOF
COMPOSE_PROJECT_NAME=galera-as-$HAPROXY_NODE_NAME
HAPROXY_NODE_NAME=$HAPROXY_NODE_NAME
EOF

cat >"$APP_DIR/haproxy/haproxy.active-standby.cfg" <<EOF
global
    log stdout format raw local0
    maxconn 2048

defaults
    log global
    mode tcp
    option tcplog
    timeout connect 2s
    timeout client 30s
    timeout server 30s

frontend mysql_write
    bind *:3306
    default_backend mysql_write_path

backend mysql_write_path
    mode tcp
    balance first
    option mysql-check user haproxy_check
    default-server inter 1s fall 2 rise 1 on-marked-down shutdown-sessions
    server db1 $DB1_HOST:3306 check
    server db2 $DB2_HOST:3306 check backup
    server db3 $DB3_HOST:3306 check backup

frontend mysql_read
    bind *:3307
    default_backend mysql_read_path

backend mysql_read_path
    mode tcp
    balance first
    option mysql-check user haproxy_check
    default-server inter 1s fall 2 rise 1 on-marked-down shutdown-sessions
    server db2 $DB2_HOST:3306 check
    server db3 $DB3_HOST:3306 check backup
    server db1 $DB1_HOST:3306 check backup

listen stats
    bind *:8404
    mode http
    stats enable
    stats uri /
    stats refresh 5s
EOF

chmod 0644 "$APP_DIR/.env" "$APP_DIR/haproxy/haproxy.active-standby.cfg"
chown -R ubuntu:ubuntu "$APP_DIR"

cd "$APP_DIR"
docker compose --env-file .env pull
docker compose --env-file .env up -d
docker compose ps
