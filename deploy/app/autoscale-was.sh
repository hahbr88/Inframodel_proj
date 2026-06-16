#!/bin/bash

# 💡 [필수 확인] compose.yaml 파일이 있는 도커 배포 디렉토리 경로로 이동합니다.
cd /home/docker/Inframodel_proj/deploy/app

# ================= 설정 구간 =================
ADM_NAME="was"

CPU_UP_THRESHOLD=20   # Scale-out 기준 (80% 초과)
CPU_DOWN_THRESHOLD=5 # Scale-in 기준 (20% 미만)

MIN_REPLICAS=1
MAX_REPLICAS=5
# =============================================

# 1. 특정 서비스의 평균 CPU 사용량을 계산하는 함수 (이름 매칭 규칙 보완)
get_avg_cpu() {
    local adm_name=$1
    # 앞뒤에 접두사(app-)나 언더바(_), 하이픈(-)이 붙어도 유연하게 잡히도록 정규식 수정
    /usr/bin/docker stats --no-stream --format "{{.Name}} {{.CPUPerc}}" | \
    grep -E ".*${adm_name}[-_][0-9]+" | sed 's/%//g' | \
    awk '{sum+=$2; count++} END {if (count > 0) print sum/count; else print 0}'
}

# 2. 현재 실행 중인 서비스별 컨테이너 개수 확인 함수 (이름 필터링 보완)
get_current_replicas() {
    local adm_name=$1
    /usr/bin/docker ps --filter "name=${adm_name}" --format "{{.Names}}" | wc -l
}

# 현재 상태 수집
CPU_ADM=$(get_avg_cpu $ADM_NAME)
REP_ADM=$(get_current_replicas $ADM_NAME)

# 초기 타겟 개수는 현재 개수로 설정 (변화가 없으면 유지)
TARGET_ADM=$REP_ADM

echo "📊 [$(date '+%Y-%m-%d %H:%M:%S')] $ADM_NAME: CPU ${CPU_ADM}% (${REP_ADM}대)"

# 3. ADM 스케일링 로직
if (( $(echo "$CPU_ADM > $CPU_UP_THRESHOLD" | bc -l) )) && [ "$REP_ADM" -lt "$MAX_REPLICAS" ]; then
    TARGET_ADM=$((REP_ADM + 1))
    echo "⚠️ $ADM_NAME 과부하! Scale-out 대상 (현재 $REP_ADM -> 변경 $TARGET_ADM)"
elif (( $(echo "$CPU_ADM < $CPU_DOWN_THRESHOLD" | bc -l) )) && [ "$REP_ADM" -gt "$MIN_REPLICAS" ]; then
    TARGET_ADM=$((REP_ADM - 1))
    echo "📉 $ADM_NAME 여유. Scale-in 대상 (현재 $REP_ADM -> 변경 $TARGET_ADM)"
fi

# 4. 변경 사항이 있을 때만 docker compose 실행 (절대 경로 적용)
if [ "$TARGET_ADM" -ne "$REP_ADM" ]; then
    echo "🚀 스케일링 명령 실행 중..."
    /usr/bin/docker compose up -d --scale ${ADM_NAME}=${TARGET_ADM}
else
    echo "✅ 자원 안정적. 변경 사항 없음."
fi
