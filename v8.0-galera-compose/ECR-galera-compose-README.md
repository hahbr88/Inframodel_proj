# MariaDB Galera Cluster 3노드 Docker Compose 구축 가이드

## 1. 범위

이 문서는 Web, WAS, Redis를 제외하고 **MariaDB Galera Cluster 3노드**만 구축한다.

| 역할 | 컨테이너 | Docker IP | 호스트 포트 | 정책 |
|---|---|---:|---:|---|
| Preferred Writer | `galera-node1` | `172.30.0.11` | `3306` | `read_only=OFF` |
| Read Node | `galera-node2` | `172.30.0.12` | `3307` | `read_only=ON` |
| Read Node | `galera-node3` | `172.30.0.13` | `3308` | `read_only=ON` |

> 세 컨테이너가 하나의 Docker 호스트에서 실행되므로 **컨테이너/DB 프로세스 장애에는 대응하지만 Docker 호스트 장애에는 대응하지 못한다.** 실제 호스트 수준 HA는 노드를 서로 다른 VM 또는 EC2에 분산해야 한다.

## 2. 사전 조건

- Ubuntu 22.04 또는 24.04
- Docker Engine과 Docker Compose Plugin 설치 완료
- 권장 여유 자원: 4 vCPU, RAM 8 GB 이상, 디스크 30 GB 이상
- 호스트의 기존 네트워크가 `172.30.0.0/24`를 사용하지 않아야 함

확인:

```bash
docker --version
docker compose version
ip route | grep 172.30.0.0 || true
```

`172.30.0.0/24`가 이미 사용 중이면 `compose.yaml`과 `config/60-galera-common.cnf`, 각 노드 설정의 IP를 함께 변경한다.

## 3. 파일 준비

```bash
cd galera-compose-guide
cp .env.example .env
mkdir -p secrets
```

비밀번호 생성:

```bash
openssl rand -hex 24 | tr -d '\n' > secrets/root_password.txt
openssl rand -hex 24 | tr -d '\n' > secrets/app_password.txt
openssl rand -hex 24 | tr -d '\n' > secrets/sst_password.txt
chmod 600 secrets/*.txt
```

`.env` 수정:

```dotenv
COMPOSE_PROJECT_NAME=three-tier-galera
MARIADB_DATABASE=appdb
MARIADB_USER=appuser
DB_BIND_IP=0.0.0.0
GALERA_BOOTSTRAP_NODE1=0
```

- `DB_BIND_IP=0.0.0.0`: 외부 WAS 호스트에서 접근 가능
- 로컬 호스트에서만 시험할 경우 `DB_BIND_IP=127.0.0.1`
- 외부 공개망 전체에 3306~3308을 허용하면 안 됨. UFW 또는 AWS Security Group에서 WAS 서버 IP/보안 그룹만 허용한다.

## 4. 설정 검증

```bash
docker compose config >/dev/null
docker compose build
```

설정 오류가 없으면 다음 단계로 이동한다.

## 5. 최초 클러스터 배포

```bash
./scripts/bootstrap.sh
```

스크립트 동작 순서:

1. `galera-node1`에만 `--wsrep-new-cluster`를 일시 적용하여 새 Primary Component 생성
2. node2 합류 및 동기화 대기
3. node3 합류 및 동기화 대기
4. node1을 bootstrap 옵션 없이 재생성하여 정상 운영 상태로 전환
5. 세 노드 상태 출력

정상 결과 기준:

- 세 노드 `CLUSTER_SIZE=3`
- `CLUSTER_STATUS=Primary`
- `LOCAL_STATE=Synced`
- `READY=ON`
- node1 `READ_ONLY=0`, node2·node3 `READ_ONLY=1`

## 6. 상태 확인

```bash
docker compose ps
./scripts/status.sh
```

개별 노드 로그:

```bash
docker compose logs --tail=200 galera-node1
docker compose logs --tail=200 galera-node2
docker compose logs --tail=200 galera-node3
```

실시간 로그:

```bash
docker compose logs -f
```

## 7. 복제 검증

```bash
./scripts/replication-test.sh
```

node1에서 생성·삽입한 데이터가 node2와 node3에서 동일하게 조회되어야 한다.

직접 상태 쿼리:

```bash
ROOT_PASSWORD="$(cat secrets/root_password.txt)"

docker exec galera-node1 mariadb -uroot -p"$ROOT_PASSWORD" -e "
SHOW GLOBAL STATUS WHERE Variable_name IN (
  'wsrep_cluster_size',
  'wsrep_cluster_status',
  'wsrep_connected',
  'wsrep_ready',
  'wsrep_local_state_comment'
);"
```

## 8. 읽기 전용 노드 검증

```bash
APP_PASSWORD="$(cat secrets/app_password.txt)"

docker exec galera-node2 mariadb \
  -u"$(grep '^MARIADB_USER=' .env | cut -d= -f2-)" \
  -p"$APP_PASSWORD" \
  "$(grep '^MARIADB_DATABASE=' .env | cut -d= -f2-)" \
  -e "INSERT INTO galera_test(node_name) VALUES ('node2-write-test');"
```

정상적으로 통제되면 `read_only` 관련 오류가 발생해야 한다.

> Galera 자체는 multi-primary이므로 node2·node3도 기술적으로 쓰기가 가능하다. 이 구성은 `read_only=ON`과 애플리케이션 연결 정책을 이용해 Preferred Writer/Read Node 방식으로 통제한다.

## 9. 접속 정보

Docker 호스트 주소가 `192.168.100.20`인 예:

| 용도 | 호스트 | 포트 |
|---|---|---:|
| Write | `192.168.100.20` | `3306` |
| Read 1 | `192.168.100.20` | `3307` |
| Read 2 | `192.168.100.20` | `3308` |

MariaDB 클라이언트 시험:

```bash
mariadb -h 192.168.100.20 -P 3306 -u appuser -p appdb
mariadb -h 192.168.100.20 -P 3307 -u appuser -p appdb
mariadb -h 192.168.100.20 -P 3308 -u appuser -p appdb
```

## 10. 단일 노드 재시작

나머지 두 노드가 정상일 때는 bootstrap 옵션을 사용하지 않는다.

```bash
docker compose restart galera-node2
./scripts/status.sh
```

동기화가 오래 걸리면:

```bash
docker compose logs -f galera-node2
```

로그에서 `IST` 또는 `SST` 진행 상태를 확인한다.

## 11. Writer 장애와 수동 전환

node1 장애 시험:

```bash
docker compose stop galera-node1
./scripts/status.sh
```

클러스터는 node2와 node3의 quorum으로 `Primary`, 크기 2를 유지해야 한다. 그러나 두 노드가 `read_only=ON`이므로 애플리케이션 쓰기는 차단된다.

node2를 임시 Writer로 전환:

```bash
ROOT_PASSWORD="$(cat secrets/root_password.txt)"
docker exec galera-node2 mariadb -uroot -p"$ROOT_PASSWORD" \
  -e "SET GLOBAL read_only=OFF;"
```

node1 복귀:

```bash
docker compose start galera-node1
./scripts/status.sh
```

node1 동기화 완료 후 node2를 다시 Read Node로 전환:

```bash
docker exec galera-node2 mariadb -uroot -p"$ROOT_PASSWORD" \
  -e "SET GLOBAL read_only=ON;"
```

`config/61-node2.cnf`에는 `read_only=ON`이 있으므로 node2 재시작 시에도 읽기 전용으로 돌아간다.

## 12. 전체 클러스터 정상 종료와 재기동

전체 종료:

```bash
./scripts/stop-cluster.sh
```

이 스크립트는 node3 → node2 → node1 순으로 종료하여 node1이 마지막 정상 노드가 되도록 한다.

재기동:

```bash
./scripts/bootstrap.sh
```

전체 노드가 내려간 상태에서는 정상 `docker compose up -d`만으로 새 Primary Component가 자동 생성되지 않는다. 마지막 정상 노드 하나를 선택해 bootstrap해야 한다.

## 13. 비정상 전체 종료 후 복구

### 13.1 grastate.dat 확인

```bash
for volume in galera-node1-data galera-node2-data galera-node3-data; do
  echo "=== $volume ==="
  docker run --rm -v "$volume":/var/lib/mysql alpine:3.21 \
    cat /var/lib/mysql/grastate.dat
done
```

`safe_to_bootstrap: 1`인 노드를 찾는다. 해당 노드가 node1이면 `./scripts/bootstrap.sh`를 사용할 수 있다.

node2 또는 node3가 안전 노드라면 그 노드에만 `GALERA_BOOTSTRAP=1`을 적용해 먼저 기동해야 한다. 두 노드 이상에 bootstrap을 적용하면 안 된다.

### 13.2 모든 노드가 safe_to_bootstrap=0인 경우

각 볼륨에서 복구 위치를 확인한다.

```bash
docker run --rm --entrypoint mariadbd \
  -v galera-node1-data:/var/lib/mysql \
  mariadb:11.8.8 \
  --user=mysql \
  --datadir=/var/lib/mysql \
  --wsrep-provider=/usr/lib/galera/libgalera_smm.so \
  --wsrep-recover
```

node2와 node3도 동일하게 실행하여 로그의 `Recovered position`을 비교한다. **가장 큰 seqno를 가진 노드 하나만** `safe_to_bootstrap: 1`로 변경한 후 bootstrap한다.

예를 들어 node1이 가장 최신일 때:

```bash
docker run --rm -v galera-node1-data:/var/lib/mysql alpine:3.21 sh -c \
  "sed -i 's/safe_to_bootstrap: 0/safe_to_bootstrap: 1/' /var/lib/mysql/grastate.dat"

./scripts/bootstrap.sh
```

최신 노드 판단 없이 `safe_to_bootstrap`을 임의 변경하면 데이터 유실이 발생할 수 있다.

## 14. 백업

Read Node인 node2에서 논리 백업:

```bash
mkdir -p backup
ROOT_PASSWORD="$(cat secrets/root_password.txt)"

docker exec galera-node2 mariadb-dump \
  -uroot -p"$ROOT_PASSWORD" \
  --all-databases \
  --single-transaction \
  --routines \
  --events \
  --triggers \
  > "backup/all-$(date +%F-%H%M%S).sql"
```

백업 파일 확인:

```bash
ls -lh backup/
```

## 15. 데이터 삭제 주의

다음 명령은 컨테이너와 네트워크만 제거하고 named volume은 유지한다.

```bash
docker compose down
```

다음 명령은 **세 노드의 DB 데이터를 전부 삭제**한다.

```bash
docker compose down -v
```

운영 데이터가 있으면 `-v`를 사용하지 않는다.

## 16. 방화벽 기준

동일 Docker 호스트 내부의 Galera 통신은 bridge network에서 처리되므로 호스트에 4444/4567/4568을 공개할 필요가 없다.

외부 WAS 서버에는 다음 클라이언트 포트만 허용한다.

- TCP 3306: Preferred Writer
- TCP 3307: Read Node 1
- TCP 3308: Read Node 2

UFW 예시에서 WAS 서버 주소가 `192.168.100.10`인 경우:

```bash
sudo ufw allow from 192.168.100.10 to any port 3306 proto tcp
sudo ufw allow from 192.168.100.10 to any port 3307 proto tcp
sudo ufw allow from 192.168.100.10 to any port 3308 proto tcp
sudo ufw status numbered
```

## 17. 최종 검증 체크리스트

- [ ] `docker compose ps`에서 세 컨테이너가 `healthy`
- [ ] 세 노드의 `wsrep_cluster_size=3`
- [ ] `wsrep_cluster_status=Primary`
- [ ] `wsrep_local_state_comment=Synced`
- [ ] `wsrep_ready=ON`
- [ ] node1 `read_only=OFF`
- [ ] node2·node3 `read_only=ON`
- [ ] node1 입력 데이터가 node2·node3에서 조회됨
- [ ] node2·node3의 appuser 쓰기가 거부됨
- [ ] node1 중지 후 node2·node3가 크기 2의 Primary 상태 유지
- [ ] 전체 정상 종료 후 node1 기준 bootstrap 재기동 성공
