# Integrated WAS

FastAPI 기반 CQRS 통합 WAS입니다. DB 모드와 날씨 데이터 모드를 독립적으로
선택할 수 있습니다.

## 구조

```text
app/
├── commands/        # 상태 변경 API, DTO, 서비스
├── queries/         # 읽기 API, DTO, 서비스
├── core/            # 환경 설정, Writer/Reader 세션, 보안
├── domain/          # SQLAlchemy 도메인 모델
├── infrastructure/  # DB 저장소, Redis 캐시, 기상청 API
└── utils/           # 기상청 발표 시각 계산
```

Command와 Query는 각자의 라우터와 서비스, 스키마를 사용합니다. 공유 모델과
외부 시스템 접근은 `domain` 및 `infrastructure`에만 둡니다.

## 현재 권장 실행: Mock 모드

```bash
cd integrated-was
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

기본값인 `DATA_MODE=mock`에서는 DB, Redis, 기상청 인증키가 모두 없어도
`http://localhost:8000/docs`에서 전체 API를 확인할 수 있습니다.
초기 계정은 로컬 확인용 `admin` / `password123`입니다. 운영에서는 초기화
코드를 마이그레이션/시드 작업으로 대체하고 기본 계정을 제거해야 합니다.
예약 생성, 취소, 목록 조회에는 로그인 시 발급되는 HttpOnly 쿠키가 필요합니다.

mock 원본 데이터는 [app/data/mock_data.json](app/data/mock_data.json)에 있습니다.
기상청 `TourStnInfoService1` 응답 필드에 맞춰 정규화한 개발용 샘플이며, 실제
서비스 키가 준비되면 받은 응답 스냅샷으로 교체하면 됩니다.

mock 모드의 예약 변경은 프로세스 메모리에만 저장됩니다. 서버를 재시작하면
`mock_data.json`의 초기 상태로 돌아가므로 개발 및 화면 연동 검증에 적합합니다.

## 기상청 정기 수집

동네예보는 하루 8회 발표되므로 사용자 요청마다 기상청을 호출할 필요가
없습니다. VM 크론이 발표 10분 후 데이터를 한 번 수집하고, WAS는 생성된
스냅샷 파일만 읽도록 설정할 수 있습니다.

```dotenv
DATA_MODE=mock
WEATHER_MODE=snapshot
KMA_SERVICE_KEY=공공데이터포털_Decoding_인증키
KMA_SNAPSHOT_PATH=./data/kma_snapshot.json
```

최초 스냅샷 수동 생성:

```bash
source .venv/bin/activate
python -m app.jobs.collect_kma
```

VM의 `crontab -e`에는 다음 작업을 등록합니다. VM 시스템 시간이 UTC여도
`CRON_TZ=Asia/Seoul` 기준으로 실행됩니다.

```cron
CRON_TZ=Asia/Seoul
10 2,5,8,11,14,17,20,23 * * * cd /opt/integrated-was && .venv/bin/python -m app.jobs.collect_kma >> kma-collector.log 2>&1
```

정확한 경로 예시는 [cron.example](cron.example)에 있습니다. 기상청 발표
정각에는 데이터가 아직 준비되지 않을 수 있어 10분 뒤 실행하며, 실패하면
기본 3회, 60초 간격으로 재시도합니다.

## DB 확정 후 전환

MariaDB 비동기 연결 예시는 다음과 같습니다.

```dotenv
DATA_MODE=database
WEATHER_MODE=snapshot
WRITE_DATABASE_URL=mysql+asyncmy://app:password@db-master:3306/integrated
READ_DATABASE_URL=mysql+asyncmy://app:password@db-replica:3306/integrated
REDIS_URL=redis://redis:6379/0
KMA_SERVICE_KEY=issued-service-key
```

서비스와 API 코드는 수정하지 않고 환경 변수만 바꿉니다.
`POST`, `DELETE`, 로그인은 `WRITE_DATABASE_URL`을 사용합니다. `GET` 요청은
`READ_DATABASE_URL`을 사용하므로 복제 지연이 있을 때 생성 직후 조회 결과가
잠시 보이지 않을 수 있습니다. 이것은 비동기 복제 환경의 정상적인 eventual
consistency 특성입니다.

## API

| Method | Path | 역할 |
| --- | --- | --- |
| `POST` | `/api/auth/login` | Command: 로그인/JWT 쿠키 발급 |
| `POST` | `/api/auth/logout` | Command: 쿠키 제거 |
| `POST` | `/api/reservations` | Command: 예약 생성 |
| `DELETE` | `/api/reservations/{id}` | Command: 예약 취소 |
| `GET` | `/api/courses` | Query: 코스 목록 |
| `GET` | `/api/course-catalog` | Query: 예약 화면용 코스·날씨·예약 통합 목록 |
| `GET` | `/api/reservations` | Query: 예약 목록 |
| `GET` | `/api/courses/{id}/village-forecast` | Query: 관광코스별 동네예보 API |
| `GET` | `/api/courses/{id}/climate-index` | Query: 시군구별 관광기후지수 API |
| `GET` | `/api/courses/{id}/weather` | Query: 두 공공 API 통합 응답 |

`WEATHER_MODE=live`는 요청 시 기상청을 호출합니다. 동네예보는 1시간,
관광기후지수는 6시간 Redis에 캐시하지만, 발표 주기가 정해진 현재 서비스에는
`WEATHER_MODE=snapshot`과 크론 수집 방식이 더 적합합니다.

두 공공 API는 같은 `TourStnInfoService1` 서비스와 인증키를 사용하지만
operation은 각각 `getTourStnVilageFcst1`, `getCityTourClmIdx1`로 구분됩니다.

동네예보 API는 코스별로 `numOfRows=300`을 지정해 한 번에 조회합니다. 현재
검증 결과 코스 1은 256건, 코스 52는 128건이며 두 코스 요청은 수집기에서
병렬 실행됩니다. 응답의
`forecasts` 배열에는 예보시각(`forecast_at`), 관광지점, 테마, 기온, 풍향,
풍속, 하늘상태, 습도, 강수확률이 모두 포함됩니다.

KMA 원본은 동일 지점과 예보시각의 날씨를 테마별로 반복합니다. WAS는 동일한
날씨 행을 하나로 병합하고 관련 테마를 `themes` 배열로 반환합니다.

예약 탐색 화면은 `/api/course-catalog` 하나를 사용하면 됩니다. 각 코스의
기본 정보, 가장 가까운 예보시각의 기온 범위·강수확률·습도·테마 요약,
관광기후지수와 활성 예약 건수를 함께 반환합니다.
`/api/courses/{id}/village-forecast` 같은 세부 API는 상세 화면과 운영 점검용으로
유지합니다.

기본 카탈로그 응답은 각 코스의 전체 예보를 포함합니다.

```text
GET /api/course-catalog
```

전체 434개 코스에서는 응답이 약 7.5MB입니다. 목록 요약만 필요하면 다음처럼
상세 예보를 제외할 수 있습니다.

```text
GET /api/course-catalog?include_forecasts=false
```

`weather_detail_path`, `reservation_path` 같은 URL 문자열은 제거했습니다.
예약 생성은 기존 계약인 `POST /api/reservations`를 사용합니다.

코스 기준정보는 `app/data/tour_course_spots.csv`에서 읽습니다. 현재 2,785개
관광지 지점을 434개 코스로 묶으며, 각 코스에는 방문 순서, 좌표, 이동시간,
실내외 구분과 테마가 포함됩니다. KMA 수집에 성공한 코스는 공식 코스명과
지역명으로 자동 보정됩니다.

전체 날씨 수집은 코스별 요청 434회를 사용합니다. 운영 전 공공데이터포털의
일일 트래픽 한도를 확인해야 합니다. 개발 검증은 `.env`의
`KMA_COURSE_LIMIT=5`처럼 제한하고, 전체 수집이 허용될 때만 `0`으로 설정합니다.
정적 CSV에는 있지만 현재 KMA 발표분이 없는 코스는 카탈로그에서
`weather_available=false`로 반환됩니다. 날씨 제공 여부와 예약 가능 여부는
별도 정책이므로 현재 등록된 코스의 `reservation_enabled`는 true입니다.

## 테스트

```bash
pytest -q
```

Docker mock 실행도 `.env` 없이 WAS 하나만 구동합니다.

```bash
docker compose up --build
```

Docker 수집 작업을 한 번 실행하려면:

```bash
docker compose --profile collector run --rm kma-collector
```

DB 모드에서 Redis까지 함께 실행할 때는 다음 명령을 사용합니다.

```bash
DATA_MODE=database docker compose --profile database up --build
```
