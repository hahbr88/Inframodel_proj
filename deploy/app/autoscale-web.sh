#!/bin/bash

# ================= 설정 구간 =================
SVC1_NAME="web-a"
SVC2_NAME="web-b"

CPU_UP_THRESHOLD=80   # Scale-out 기준 (80% 초과)
CPU_DOWN_THRESHOLD=20 # Scale-in 기준 (20% 미만)

MIN_REPLICAS=2
MAX_REPLICAS=5
# =============================================

# 1. 특정 서비스의 평균 CPU 사용량을 계산하는 함수
get_avg_cpu() {
    local svc_name=$1
    # 실행 중인 서비스 컨테이너들의 CPU 사용량을 가져와 평균 계산
    docker stats --no-stream --format "{{.Name}} {{.CPUPerc}}" | \
    grep -E "${svc_name}-[0-9]+" | sed 's/%//g' | \
    awk '{sum+=$2; count++} END {if (count > 0) print sum/count; else print 0}'
}

# 2. 현재 실행 중인 서비스별 컨테이너 개수 확인 함수
get_current_replicas() {
    local svc_name=$1
    docker ps --filter "name=${svc_name}-[0-9]+" --format "{{.Names}}" | wc -l
}

# 현재 상태 수집
CPU_SVC1=$(get_avg_cpu $SVC1_NAME)
CPU_SVC2=$(get_avg_cpu $SVC2_NAME)

REP_SVC1=$(get_current_replicas $SVC1_NAME)
REP_SVC2=$(get_current_replicas $SVC2_NAME)

# 초기 타겟 개수는 현재 개수로 설정 (변화가 없으면 유지)
TARGET_SVC1=$REP_SVC1
TARGET_SVC2=$REP_SVC2

echo "📊 [현재 상태] $SVC1_NAME: CPU ${CPU_SVC1}% (${REP_SVC1}대) / $SVC2_NAME: CPU ${CPU_SVC2}% (${REP_SVC2}대)"

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

# 5. 변경 사항이 있을 때만 docker compose 실행
if [ "$TARGET_SVC1" -ne "$REP_SVC1" ] || [ "$TARGET_SVC2" -ne "$REP_SVC2" ]; then
    echo "🚀 스케일링 명령 실행 중..."
    docker compose up -d --scale ${SVC1_NAME}=${TARGET_SVC1} --scale ${SVC2_NAME}=${TARGET_SVC2}
else
    echo "✅ 자원 안정적. 변경 사항 없음."
fi
