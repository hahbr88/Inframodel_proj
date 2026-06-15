#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

[[ -f $ENV_FILE ]] || {
  echo "오류: $ENV_FILE 파일이 없습니다. WAS를 먼저 배포하세요." >&2
  exit 1
}

if ! grep -Eq '^KMA_SERVICE_KEY=.+$' "$ENV_FILE"; then
  echo "오류: $ENV_FILE의 KMA_SERVICE_KEY를 설정하세요." >&2
  exit 1
fi

cd "$SCRIPT_DIR"

run_options=(--rm)
if [[ -n ${KMA_COURSE_LIMIT:-} ]]; then
  run_options+=(-e "KMA_COURSE_LIMIT=$KMA_COURSE_LIMIT")
fi
if [[ -n ${KMA_COLLECTION_CONCURRENCY:-} ]]; then
  run_options+=(-e "KMA_COLLECTION_CONCURRENCY=$KMA_COLLECTION_CONCURRENCY")
fi

docker compose --profile collector run "${run_options[@]}" kma-collector
