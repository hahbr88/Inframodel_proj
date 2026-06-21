# Galera + Dual HAProxy VM Architecture

이 폴더는 기존 `v8.0-haproxy-galera-compose`를 수정하지 않고 새로 만든 VM 검증용 구성이다. 이 버전은 VIP와 keepalived를 사용하지 않는다.

## 구조

```text
Client/WAS
  |
  +-- primary DB endpoint   -> haproxy1 192.168.100.11
  |
  +-- secondary DB endpoint -> haproxy2 192.168.100.12

haproxy1, haproxy2는 같은 backend 정책을 가진다.

Write endpoint: HAProxy:3306 -> db1 primary -> db2 backup -> db3 backup
Read endpoint : HAProxy:3307 -> db2 primary -> db3 backup -> db1 backup

db1 192.168.100.30 read_only=OFF
db2 192.168.100.40 read_only=OFF
db3 192.168.100.50 read_only=OFF
```
```
                ┌──────────────────────────┐
                │        HAProxy1          │
                │     192.168.100.11       │
                │   active 후보            │
                └────────────┬─────────────┘
                             │
                             │ 같은 HAProxy 설정
                             │
                ┌────────────▼─────────────┐
                │        HAProxy2          │
                │     192.168.100.12       │
                │   standby 후보           │
                └────────────┬─────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌───────────────────┐                    ┌───────────────────┐
│ Write Backend     │                    │ Read Backend      │
│ mysql_write_path  │                    │ mysql_read_path   │
└─────────┬─────────┘                    └─────────┬─────────┘
          │                                        │
          │ 우선순위 기반                           │ 우선순위 기반
          │ round robin 없음                        │ round robin 없음
          │                                        │
          ▼                                        ▼

Write 우선순위                         Read 우선순위

1. db1                                1. db2
   192.168.100.30                        192.168.100.40
   read_only=OFF                         read_only=OFF

2. db2                                2. db3
   192.168.100.40                        192.168.100.50
   read_only=OFF                         read_only=OFF

3. db3                                3. db1
   192.168.100.50                        192.168.100.30
   read_only=OFF                         read_only=OFF
```

```
                 Galera 동기 복제 관계

┌───────────────────┐
│ db1               │
│ 192.168.100.30    │
│ write 1순위       │
└─────────┬─────────┘
          │
          │ wsrep
          │
┌─────────▼─────────┐
│ db2               │
│ 192.168.100.40    │
│ read 1순위        │
│ write 2순위       │
└─────────┬─────────┘
          │
          │ wsrep
          │
┌─────────▼─────────┐
│ db3               │
│ 192.168.100.50    │
│ standby backup    │
│ write 3순위       │
│ read 2순위        │
└───────────────────┘
```

```
장애 시 HAProxy 라우팅

정상:
write -> db1
read  -> db2

db1 장애:
write -> db2
read  -> db2

db2 장애:
write -> db1
read  -> db3

db1 + db2 장애:
write -> db3
read  -> db3
```






## 검토 결과

VIP 없이 구성 가능하다. 단, VIP를 제거하면 HAProxy 앞의 단일 접속점도 사라진다.

따라서 둘 중 하나가 필요하다.

- WAS가 `haproxy1`을 1순위, `haproxy2`를 2순위 DB host로 설정한다.
- 또는 AWS NLB 같은 외부 로드밸런서가 `haproxy1`, `haproxy2`를 target으로 가진다.

HAProxy 내부 DB 라우팅은 다음 정책이다.

- HAProxy backend에는 round robin을 쓰지 않고 `balance first`와 `backup` 우선순위를 사용한다.
- 평상시 write는 db1만 받는다.
- db1 장애 시 write는 db2로 이동한다.
- db1과 db2가 모두 장애이면 write는 db3로 이동한다.
- 평상시 read는 db2만 받는다.
- db2 장애 시 read는 db3로 이동한다.
- db2와 db3이 모두 장애이면 read는 db1로 이동한다.

DB 3대는 모두 `read_only=OFF`다. 그래서 별도 promotion 없이 HAProxy만으로 DB 장애 전환이 가능하다.

주의할 점은 db2와 db3도 DB 레벨에서는 쓰기가 가능하다는 것이다. 운영 정책은 HAProxy와 네트워크 접근 제어로 강제한다.

- WAS는 HAProxy만 사용한다.
- WAS에서 db1/db2/db3의 3306으로 직접 접속하지 못하게 막는다.
- DB 3306은 HAProxy VM과 Galera 노드 간 통신만 허용한다.
- Galera multi-primary 특성상 애플리케이션에는 deadlock/certification conflict 재시도 로직이 필요하다.

## VM 역할

| VM | IP | 역할 |
|---|---:|---|
| haproxy1 | `192.168.100.11` | HAProxy 1순위 접속 대상 |
| haproxy2 | `192.168.100.12` | HAProxy 2순위 접속 대상 |
| db1 | `192.168.100.30` | write primary, read final backup |
| db2 | `192.168.100.40` | read primary, write first backup |
| db3 | `192.168.100.50` | write/read standby backup |

## 파일

| 파일 | 용도 |
|---|---|
| `compose.vm-db.yaml` | db1/db2/db3 공통 Docker Compose |
| `compose.vm-haproxy.yaml` | haproxy1/haproxy2 공통 Docker Compose |
| `haproxy/haproxy.active-standby.cfg` | write/read endpoint와 backup 서버 정의 |
| `.env.vm-db*.example` | DB VM별 환경 변수 |
| `.env.vm-haproxy*.example` | HAProxy VM별 환경 변수 |
| `scripts/status-db.sh` | DB 노드 상태 확인 |

## 다음 문서

- [APPLY-GUIDE.md](APPLY-GUIDE.md): VM 배포 절차
- [VALIDATION.md](VALIDATION.md): 장애 검증 절차
