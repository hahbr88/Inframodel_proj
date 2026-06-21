#!/bin/bash

# 💡 [필수 수정] compose.yaml 파일이 있는 도커 배포 디렉토리 경로로 이동합니다.
cd /app

# ================= 설정 구간 =================
SVC1_NAME="service-web"
SVC2_NAME="admin-web"

CPU_UP_THRESHOLD=15   # Scale-out 기준 (80% 초과)
CPU_DOWN_THRESHOLD=5 # Scale-in 기준 (20% 미만)

MIN_REPLICAS=1
MAX_REPLICAS=5
# =============================================

# 1. 특정 서비스의 평균 CPU 사용량을 계산하는 함수 (이름 매칭 보완)
get_avg_cpu() {
    local svc_name=$1
    # 컨테이너 이름에 서비스명이 포함된 모든 라인을 유연하게 잡도록 수정 (*_ 또는 *-)
    /usr/bin/docker stats --no-stream --format "{{.Name}} {{.CPUPerc}}" | \
    grep -E ".*${svc_name}[-_][0-9]+" | sed 's/%//g' | \
    awk '{sum+=$2; count++} END {if (count > 0) print sum/count; else print 0}'
}

# 2. 현재 실행 중인 서비스별 컨테이너 개수 확인 함수
get_current_replicas() {
    local svc_name=$1
    /usr/bin/docker ps --filter "name=${svc_name}" --format "{{.Names}}" | wc -l
}

# 현재 상태 수집
CPU_SVC1=$(get_avg_cpu $SVC1_NAME)
CPU_SVC2=$(get_avg_cpu $SVC2_NAME)

REP_SVC1=$(get_current_replicas $SVC1_NAME)
REP_SVC2=$(get_current_replicas $SVC2_NAME)

# 초기 타겟 개수는 현재 개수로 설정
TARGET_SVC1=$REP_SVC1
TARGET_SVC2=$REP_SVC2

echo "📊 [$(date '+%Y-%m-%d %H:%M:%S')] $SVC1_NAME: CPU ${CPU_SVC1}% (${REP_SVC1}대) / $SVC2_NAME: CPU ${CPU_SVC2}% (${REP_SVC2}대)"

# 3. SVC1 스케일링 로직
if (( $(echo "$CPU_SVC1 > $CPU_UP_THRESHOLD" | bc -l) )) && [ "$REP_SVC1" -lt "$MAX_REPLICAS" ]; then
    TARGET_SVC1=$((REP_SVC1 + 1))
    echo "⚠️ $SVC1_NAME 과부하! Scale-out 대상 (현재 $REP_SVC1 -> 변경 $TARGET_SVC1)"
elif (( $(echo "$CPU_SVC1 < $CPU_DOWN_THRESHOLD" | bc -l) )) && [ "$REP_SVC1" -gt "$MIN_REPLICAS" ]; then
    TARGET_SVC1=$((REP_SVC1 - 1))
    echo "📉 $SVC1_NAME 여유. Scale-in 대상 (현재 $REP_SVC1 -> 변경 $TARGET_SVC1)"
fi

# 4. SVC2 스케일링 로직
if (( $(echo "$CPU_SVC2 > $CPU_UP_THRESHOLD" | bc -l) )) && [ "$REP_SVC2" -lt "$MAX_REPLICAS" ]; then
    TARGET_SVC2=$((REP_SVC2 + 1))
    echo "⚠️ $SVC2_NAME 과부하! Scale-out 대상 (현재 $REP_SVC2 -> 변경 $TARGET_SVC2)"
elif (( $(echo "$CPU_SVC2 < $CPU_DOWN_THRESHOLD" | bc -l) )) && [ "$REP_SVC2" -gt "$MIN_REPLICAS" ]; then
    TARGET_SVC2=$((REP_SVC2 - 1))
    echo "📉 $SVC2_NAME 여유. Scale-in 대상 (현재 $REP_SVC2 -> 변경 $TARGET_SVC2)"
fi

# 5. 변경 사항이 있을 때만 docker compose 실행 (절대 경로 지정)
if [ "$TARGET_SVC1" -ne "$REP_SVC1" ] || [ "$TARGET_SVC2" -ne "$REP_SVC2" ]; then
    echo "🚀 스케일링 명령 실행 중..."
    /usr/bin/docker compose up -d --scale ${SVC1_NAME}=${TARGET_SVC1} --scale ${SVC2_NAME}=${TARGET_SVC2}
else
    echo "✅ 자원 안정적. 변경 사항 없음."
fi
