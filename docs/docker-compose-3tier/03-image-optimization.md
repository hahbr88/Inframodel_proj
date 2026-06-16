# Docker 이미지 경량화 전략

## 1. 목적

Docker Compose 배포 구조에서 실제 운영 이미지 크기를 확인하고, 경량화 대상과
비대상 범위를 판단한다. 목표는 무조건 최소 크기 이미지를 만드는 것이 아니라,
기능 안정성을 유지하면서 불필요한 운영 의존성과 파일을 제거하는 것이다.

## 2. 현재 이미지 크기

app-vm에서 확인한 이미지 크기:

```text
CONTAINER           REPOSITORY        SIZE
app-admin-web-1     app-admin-web     21.8MB
app-gateway-1       nginx             21.6MB
app-service-web-1   app-service-web   21.9MB
app-was-1           app-was           74.8MB
```

`service-web`, `admin-web`, `gateway`는 최종 이미지가 `nginx:alpine` 기반이며
정적 파일만 포함한다. 이미 22MB 수준이므로 경량화 우선순위가 낮다.

WAS와 KMA collector는 같은 `apps/integrated-was/Dockerfile`로 빌드되므로,
WAS 이미지를 줄이면 collector 이미지도 함께 줄어든다.

## 3. 크기 분석 결과

WAS 컨테이너 내부 크기:

```text
568K   /app
111M   /opt/venv
```

애플리케이션 코드는 1MB 미만이고, 대부분의 크기는 Python virtualenv에 있다.
따라서 경량화의 주 대상은 소스 파일이 아니라 Python 의존성이다.

큰 의존성:

```text
23M  sqlalchemy
21M  asyncmy
16M  uvloop
13M  pip
4.4M pydantic_core
4.0M pydantic
3.2M yaml
2.9M redis
2.9M _pytest
2.1M httptools
1.7M websockets
1.3M watchfiles
```

`sqlalchemy`, `asyncmy`, `pydantic`, `redis`, `pwdlib[argon2]` 계열은 현재 기능에
필요하다. 반면 `pytest`, `pytest-asyncio`, `watchfiles`, `websockets`는 운영
WAS 실행에는 필요하지 않다.

## 4. 적용 전략

경량화 변경은 안전 최적화와 실험 최적화로 나눈다.

| 구분 | 변경 | 판단 |
|---|---|---|
| 안전 최적화 | 테스트 의존성 분리 | 운영 런타임에 불필요하므로 적용 |
| 안전 최적화 | Dockerfile 복사 범위 축소 | 기능 영향 없이 포함 파일을 제한하므로 적용 |
| 실험 최적화 | `uvicorn[standard]` 제거 | 이미지 크기와 성능의 트레이드오프가 있어 검증 후 유지 여부 결정 |

### 4.1 운영/개발 의존성 분리

기존에는 테스트 도구가 운영 `requirements.txt`에 포함되어 있었다.

```text
pytest
pytest-asyncio
```

이를 `requirements-dev.txt`로 분리한다.

```text
requirements.txt      # 운영 이미지용
requirements-dev.txt  # 로컬 개발 및 테스트용
```

개발자는 로컬 테스트 시 다음처럼 설치한다.

```bash
pip install -r requirements-dev.txt
pytest -q
```

운영 Dockerfile은 `requirements.txt`만 설치하므로 테스트 도구가 이미지에
포함되지 않는다.

### 4.2 `uvicorn[standard]` 제거 실험

기존 설정:

```text
uvicorn[standard]==0.34.2
```

변경 설정:

```text
uvicorn==0.34.2
```

`uvicorn[standard]`는 다음 선택 의존성을 함께 설치한다.

```text
uvloop
httptools
watchfiles
websockets
PyYAML
python-dotenv
```

현재 프로젝트는 WebSocket 기능을 사용하지 않는다. 다음 검색에서 앱 코드 내
사용처가 없음을 확인했다.

```bash
grep -RInE "WebSocket|websocket|websockets|@.*websocket|ws://" apps \
  --exclude-dir=node_modules \
  --exclude-dir=dist \
  --exclude-dir=.venv \
  --exclude-dir=.pytest_cache \
  --exclude-dir=.ruff_cache
```

따라서 `websockets`, `watchfiles` 등은 운영 이미지에서 제외할 후보로 볼 수
있다.

단, `uvloop`, `httptools`는 성능 최적화용이다. 제거하면 기본 Python
`asyncio`와 `h11` 기반으로 동작하므로 응답시간, CPU 사용률, 처리량이 나빠질 수
있다. 따라서 이 변경은 확정 최적화가 아니라 실험 최적화로 관리한다.

유지 조건:

- HTTP API 기능 검증을 통과한다.
- 간단한 부하 테스트에서 실패 요청이 없다.
- 평균 응답시간이 기존 대비 크게 악화되지 않는다.
- WAS CPU 사용률이 기존 대비 과도하게 증가하지 않는다.

복구 조건:

- 요청 실패 또는 timeout이 발생한다.
- 평균 응답시간이 기존 대비 20~30% 이상 증가한다.
- WAS CPU 사용률이 뚜렷하게 증가한다.
- 동시 요청 처리량이 의미 있게 감소한다.

복구가 필요하면 `requirements.txt`를 다시 다음처럼 되돌린다.

```text
uvicorn[standard]==0.34.2
```

### 4.3 Dockerfile 복사 범위 축소

기존:

```dockerfile
COPY . .
```

변경:

```dockerfile
COPY main.py .
COPY app ./app
```

현재 `.dockerignore`가 대부분의 불필요 파일을 막고 있으므로 크기 절감 효과는
크지 않다. 하지만 런타임 이미지에 문서, 테스트 파일, 로컬 산출물이 실수로
포함될 가능성을 줄인다.

## 5. 보류한 최적화

### 5.1 `pip` 제거

WAS venv 안의 `pip`는 약 13MB다. 운영 컨테이너에서 패키지 설치를 하지 않으므로
제거할 수 있다.

예시:

```dockerfile
RUN pip install --no-cache-dir --no-compile -r requirements.txt \
    && pip uninstall -y pip setuptools wheel
```

다만 일부 런타임 진단이나 패키지 메타데이터 확인에 영향을 줄 수 있으므로,
이번 1차 경량화에서는 보류한다. `requirements` 분리와 `uvicorn[standard]` 제거
실험 후 크기와 성능을 다시 측정한 다음 추가 적용 여부를 판단한다.

### 5.2 더 작은 Python 베이스 이미지

`python:3.12-slim`보다 더 작은 distroless 또는 Alpine 기반 이미지를 검토할 수
있다. 하지만 `asyncmy`, `greenlet`, `argon2`처럼 네이티브 확장이 포함되어 있어
빌드 및 런타임 호환성 리스크가 커진다.

현재는 안정성이 더 중요하므로 `python:3.12-slim`을 유지한다.

## 6. 검증 절차

app-vm에서 최신 코드를 받은 뒤 WAS 계열 이미지를 다시 빌드한다.

```bash
cd ~/Inframodel_proj
git pull
cd deploy/app

docker compose build was kma-collector
docker compose up -d --force-recreate was
```

크기 비교:

```bash
docker compose images
docker run --rm app-was du -h -d 1 /opt/venv | sort -h
docker run --rm app-was du -h -d 1 /opt/venv/lib/python3.12/site-packages | sort -h | tail -30
```

기능 확인:

```bash
curl -s http://127.0.0.1/api/course-catalog | head
docker compose exec gateway wget -qO- http://was:8000/
```

KMA collector 확인:

```bash
KMA_COURSE_LIMIT=3 ./collect-weather.sh
```

## 7. 판단 기준

안전 최적화 변경은 다음 조건을 만족해야 유지한다.

- `was` 컨테이너가 healthy 상태로 기동한다.
- `gateway -> was` 내부 통신이 정상이다.
- `/api/course-catalog`가 DB 기반 응답을 반환한다.
- KMA collector가 소량 수집에 성공한다.
- 이미지 크기가 기존 `app-was: 74.8MB`보다 감소한다.

`uvicorn[standard]` 제거 실험은 위 기능 조건에 더해 응답시간과 CPU 사용률을
함께 본다. 기능은 정상이어도 성능 저하가 확인되면 `uvicorn[standard]`로
되돌린다.

이 조건 중 하나라도 깨지면 해당 변경은 되돌리고, 의존성 제거 범위를 다시
검토한다.
