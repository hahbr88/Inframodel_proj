#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-northeast-2}"
IMAGE_TAG="${IMAGE_TAG:-v1.0}"
ECR_REGISTRY="${ECR_REGISTRY:-}"

[[ -n $ECR_REGISTRY ]] || {
  echo "ECR_REGISTRY를 지정하세요. 예: 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com" >&2
  exit 1
}

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

build_and_push() {
  local name="$1"
  local context="$2"

  docker build -t "$name:$IMAGE_TAG" "$context"
  docker tag "$name:$IMAGE_TAG" "$ECR_REGISTRY/$name:$IMAGE_TAG"
  docker tag "$name:$IMAGE_TAG" "$ECR_REGISTRY/$name:stable"
  docker push "$ECR_REGISTRY/$name:$IMAGE_TAG"
  docker push "$ECR_REGISTRY/$name:stable"
}

build_and_push inframodel-service-web apps/service-web
build_and_push inframodel-admin-web apps/admin-web
build_and_push inframodel-was apps/integrated-was

aws ecr list-images \
  --region "$AWS_REGION" \
  --repository-name inframodel-was
