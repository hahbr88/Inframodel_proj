#!/usr/bin/env bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
SSM_PREFIX="${SSM_PREFIX:-/inframodel/prod/web}"
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
mkdir -p "$APP_DIR/gateway"
aws s3 cp \
  "s3://$ARTIFACT_BUCKET/inframodel/prod/web/compose.yaml" \
  "$APP_DIR/compose.yaml"
aws s3 cp \
  "s3://$ARTIFACT_BUCKET/inframodel/prod/web/gateway/default.conf.template" \
  "$APP_DIR/gateway/default.conf.template"

ECR_REGISTRY="$(ssm "$SSM_PREFIX/ecr-registry")"
IMAGE_TAG="$(ssm "$SSM_PREFIX/image-tag")"
WAS_UPSTREAM_HOST="$(ssm "$SSM_PREFIX/was-upstream-host")"
WAS_UPSTREAM_PORT="$(ssm "$SSM_PREFIX/was-upstream-port")"

cat >"$APP_DIR/.env" <<EOF
ECR_REGISTRY=$ECR_REGISTRY
IMAGE_TAG=$IMAGE_TAG
HTTP_PORT=80
WAS_UPSTREAM_HOST=$WAS_UPSTREAM_HOST
WAS_UPSTREAM_PORT=$WAS_UPSTREAM_PORT
EOF

chmod 0644 "$APP_DIR/.env"
chown ubuntu:ubuntu "$APP_DIR/.env"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

cd "$APP_DIR"
docker compose --env-file .env pull
docker compose --env-file .env up -d
docker compose ps
