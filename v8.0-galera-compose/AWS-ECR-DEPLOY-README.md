# AWS ECR 기반 Galera Compose 배포 검토

## 결론

현재 Galera 클러스터 구성은 VMware 3대 분산 환경에서 데이터 연동 검증이 완료된 상태다. AWS ECR을 통해 이미지를 빌드, 저장, 배포하려면 `compose.yaml`보다는 `compose.vm.yaml`을 기준으로 배포하는 것이 맞다.

- `compose.yaml`: 한 Docker 호스트에서 Galera 컨테이너 3개를 실행하는 로컬/단일호스트 구성
- `compose.vm.yaml`: VM 또는 EC2 인스턴스 3대에 Galera 노드를 분산 실행하는 구성

AWS ECR은 Docker 이미지만 저장한다. 따라서 ECR에 이미지를 push하더라도 `.env`, `secrets/*.txt`, `config/vm/60-galera-common.cnf` 같은 Compose 실행 파일은 각 배포 대상 VM 또는 EC2에 별도로 배치해야 한다.

## 현재 compose 파일 검토 결과

현재 `compose.yaml`과 `compose.vm.yaml`에는 모두 다음 형태의 설정이 들어 있다.

```yaml
build:
  context: .
  dockerfile: Dockerfile
image: three-tier-mariadb-galera:11.8.8
```

이 구성은 로컬에서 직접 이미지를 빌드할 때는 편리하다. 하지만 ECR 배포 대상 서버에서 그대로 `docker compose up -d`를 실행하면, ECR에서 이미지를 pull하는 흐름과 로컬 `Dockerfile`로 다시 build하는 흐름이 섞일 수 있다.

ECR 기반 배포에서는 배포용 compose 파일에서 `build:`를 제거하고, `image:`를 ECR 이미지 URI로 지정하는 방식이 더 안전하다.

## 권장 compose 설정

ECR 배포용 compose에서는 다음처럼 이미지 이름을 환경 변수로 받는 것을 권장한다.

```yaml
services:
  galera:
    image: ${GALERA_IMAGE:?Set GALERA_IMAGE in .env}
```

각 VM 또는 EC2의 `.env`에는 다음 값을 추가한다.

```env
GALERA_IMAGE=123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/three-tier-mariadb-galera:11.8.8
```

`123456789012`, `ap-northeast-2`, repository 이름, tag는 실제 AWS 계정과 ECR repository에 맞게 변경한다.

## Dockerfile 검토

현재 `Dockerfile`은 ECR에 push할 이미지 구성으로 적절하다.

```dockerfile
FROM mariadb:11.8.8

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends socat rsync \
    && rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint-galera.sh /usr/local/bin/docker-entrypoint-galera.sh
COPY initdb-create-sst-user.sh /docker-entrypoint-initdb.d/01-create-sst-user.sh

RUN chmod 0755 /usr/local/bin/docker-entrypoint-galera.sh \
    && chmod 0644 /docker-entrypoint-initdb.d/01-create-sst-user.sh

ENTRYPOINT ["docker-entrypoint-galera.sh"]
CMD ["mariadbd"]
```

이미지 안에 포함되는 항목:

- MariaDB 11.8.8
- Galera SST/IST에 필요한 `socat`, `rsync`
- `docker-entrypoint-galera.sh`
- `initdb-create-sst-user.sh`

이미지 안에 포함되지 않는 항목:

- `.env`
- `secrets/*.txt`
- `config/vm/60-galera-common.cnf`
- 데이터 볼륨
- AWS Security Group 설정

## ECR 이미지 빌드 및 Push 절차

빌드 머신에서 실행한다.

```bash
cd v8.0-galera-compose

AWS_ACCOUNT_ID=123456789012
AWS_REGION=ap-northeast-2
ECR_REPOSITORY=three-tier-mariadb-galera
IMAGE_TAG=11.8.8
ECR_IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker build -t "${ECR_REPOSITORY}:${IMAGE_TAG}" .
docker tag "${ECR_REPOSITORY}:${IMAGE_TAG}" "${ECR_IMAGE}"
docker push "${ECR_IMAGE}"
```

ECR repository가 없다면 먼저 생성한다.

```bash
aws ecr create-repository \
  --region ap-northeast-2 \
  --repository-name three-tier-mariadb-galera
```

## 각 VM 또는 EC2 배포 절차

각 DB 노드에서 실행한다.

```bash
cd ~/v8.0-galera-compose

AWS_ACCOUNT_ID=123456789012
AWS_REGION=ap-northeast-2

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker compose --env-file .env -f compose.vm.yaml pull
docker compose --env-file .env -f compose.vm.yaml up -d
docker compose --env-file .env -f compose.vm.yaml ps
```

초기 클러스터 구성 순서는 기존 VMware 검증 절차와 동일하게 유지한다.

1. db1에서만 `GALERA_BOOTSTRAP=1`로 부트스트랩
2. db1이 `healthy`가 되면 db2 합류
3. db2가 `healthy`가 되면 db3 합류
4. 세 노드가 모두 `Synced` 상태가 되면 db1의 `GALERA_BOOTSTRAP=0`으로 변경
5. db1 컨테이너 재생성

## 각 노드에 필요한 로컬 파일

ECR 이미지를 사용하더라도 각 노드에는 다음 파일이 있어야 한다.

```text
v8.0-galera-compose/
├── compose.vm.yaml
├── .env
├── config/
│   └── vm/
│       └── 60-galera-common.cnf
└── secrets/
    ├── root_password.txt
    ├── app_password.txt
    └── sst_password.txt
```

세 노드의 secret 파일 값은 반드시 동일해야 한다.

```bash
sha256sum secrets/*.txt
```

## AWS Security Group 확인

EC2에서 실행할 경우 DB 노드끼리 다음 포트를 허용해야 한다.

| Port | Protocol | Purpose |
|---:|---|---|
| 3306 | TCP | MariaDB client connection |
| 4444 | TCP | Galera SST |
| 4567 | TCP | Galera replication |
| 4567 | UDP | Galera replication |
| 4568 | TCP | Galera IST |

권장 방식:

- DB 노드 Security Group끼리만 위 포트를 허용한다.
- `3306`을 전체 공개망 `0.0.0.0/0`에 열지 않는다.
- WAS 또는 애플리케이션 서버는 필요한 노드의 `3306`에만 접근하도록 제한한다.

## ECR 배포 전 체크리스트

- [ ] ECR repository가 생성되어 있다.
- [ ] `docker build`가 성공한다.
- [ ] ECR image push가 성공한다.
- [ ] `compose.vm.yaml`의 배포용 설정에서 `build:`를 제거했다.
- [ ] `image:`가 ECR URI 또는 `${GALERA_IMAGE}`를 사용한다.
- [ ] 각 노드의 `.env`에 올바른 `GALERA_IMAGE`가 들어 있다.
- [ ] 각 노드의 `.env`에 `GALERA_NODE_ADDRESS`, `GALERA_SERVER_ID`, `GALERA_NODE_NAME`이 자기 노드에 맞게 설정되어 있다.
- [ ] 세 노드의 `secrets/*.txt` 체크섬이 동일하다.
- [ ] EC2 Security Group 또는 VM 방화벽에서 Galera 포트가 허용되어 있다.
- [ ] db1 부트스트랩 후 db2, db3 순서로 합류시킨다.
- [ ] 최종적으로 세 노드 모두 `wsrep_cluster_size = 3`, `wsrep_local_state_comment = Synced` 상태다.

## 핵심 주의사항

ECR은 이미지 배포 문제만 해결한다. Galera 클러스터 안정성은 여전히 다음 항목에 의존한다.

- 노드별 고정 IP 또는 안정적인 DNS
- 세 노드 간 Galera 포트 통신
- 동일한 secret 파일
- 올바른 부트스트랩 순서
- 데이터 볼륨 보존
- `GALERA_BOOTSTRAP=1`을 한 노드에만 지정하는 운영 절차

따라서 AWS ECR 전환 시에는 이미지 배포 방식만 바꾸고, Galera 클러스터 구성과 부트스트랩 절차는 기존 VMware 검증 절차를 그대로 유지하는 것이 안전하다.
