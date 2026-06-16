#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
COLLECTOR_SCRIPT="$SCRIPT_DIR/collect-weather.sh"
LOG_FILE="$SCRIPT_DIR/kma-collector.log"
MARKER="# inframodel-kma-collector"

command -v crontab >/dev/null || {
  echo "오류: cron이 설치되어 있지 않습니다." >&2
  echo "sudo apt-get install -y cron && sudo systemctl enable --now cron" >&2
  exit 1
}

[[ -x $COLLECTOR_SCRIPT ]] || {
  echo "오류: 실행 파일을 찾지 못했습니다: $COLLECTOR_SCRIPT" >&2
  exit 1
}

temporary_file="$(mktemp)"
trap 'rm -f "$temporary_file"' EXIT

crontab -l 2>/dev/null \
  | grep -vF "$MARKER" \
  | grep -vF "$COLLECTOR_SCRIPT" >"$temporary_file" || true

cat >>"$temporary_file" <<EOF
$MARKER
CRON_TZ=Asia/Seoul
10 2,5,8,11,14,17,20,23 * * * $COLLECTOR_SCRIPT >> $LOG_FILE 2>&1
EOF

crontab "$temporary_file"
echo "날씨 수집 cron 등록 완료"
crontab -l
