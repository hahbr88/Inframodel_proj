# AWS EC2/ECR/CloudFront/Route 53 배포 검증

이 디렉터리는 VMware에서 검증한 Docker Compose 구조를 AWS에서도 실행 가능한지
확인하기 위한 배포 산출물이다.

AWS 단계에서는 Web EC2, App/WAS EC2, DB EC2를 분리한다. Web EC2는
CloudFront의 origin 역할을 하고, App/WAS EC2와 DB/HAProxy EC2는 Private
Subnet에서 내부 요청만 받는다. 외부 HTTPS 접속은 CloudFront와 ACM 인증서로
처리한다.
AWS 단계에서는 Web EC2, App/WAS EC2, DB EC2를 분리한다. Web EC2는
CloudFront의 origin 역할을 하고, App/WAS EC2와 DB/HAProxy EC2는 Private
Subnet에서 내부 요청만 받는다. 외부 HTTPS 접속은 CloudFront와 ACM 인증서로
처리한다.

## 1. 목표 구조

```text
Route 53
  -> CloudFront + ACM
  -> Public Subnet
     -> Web EC2 origin:80
        -> gateway
           /        -> service-web
           /admin/  -> admin-web
           /api/    -> Private Subnet App/WAS EC2:8000

Private Subnet
  -> App/WAS EC2
     -> was
        -> redis
     -> HAProxy/NLB:3306(write),3307(read)

Private Subnet
  -> HAProxy EC2 x2
     -> DB EC2 x3 Galera MariaDB
```

## 2. 디렉터리 구성

| 경로 | 용도 |
|---|---|
| `web/compose.yaml` | Web EC2에서 gateway, service-web, admin-web 실행 |
| `web/gateway/default.conf.template` | Web EC2 gateway Nginx 설정 |
| `app/compose.yaml` | App/WAS EC2에서 was, redis 실행 |
| `app/.env.example` | App/WAS EC2 환경변수 예시 |
| `db/compose.galera.yaml` | DB EC2에서 Galera MariaDB 실행 |
| `db/compose.haproxy.yaml` | HAProxy EC2에서 DB read/write 프록시 실행 |
| `db/user-data-galera.sh` | Galera DB 노드 User Data |
| `db/user-data-haproxy.sh` | DB HAProxy 노드 User Data |
| `user-data.sh` | EC2 초기 Docker 설치 자동화 |
| `ecr-build-push.sh` | App 이미지를 ECR에 버전 태그로 Push |
| `.github/workflows/ecr-build.yml` | `aws-ecr` 브랜치 push 시 App 이미지를 ECR에 자동 Push |

## 3. VPC와 Security Group

권장 네트워크 구성:

| 리소스 | 위치 | 외부 접근 |
|---|---|---|
| Web EC2 | Public Subnet | CloudFront origin 요청, SSH 22 제한 허용 |
| App/WAS EC2 | Private Subnet | Public IP 없음 |
| HAProxy EC2 | Private Subnet | Public IP 없음 |
| DB EC2 | Private Subnet | Public IP 없음 |

Security Group 예시:

| 대상 | Inbound |
|---|---|
| Web EC2 SG | `80/tcp` from CloudFront origin-facing prefix list, `22/tcp` from 관리자 IP |
| App/WAS EC2 SG | `8000/tcp` from Web EC2 Security Group |
| HAProxy EC2 SG | `3306/tcp`, `3307/tcp` from App/WAS EC2 Security Group |
| DB EC2 SG | `3306/tcp` from HAProxy EC2 Security Group, DB 노드 간 `4444/tcp`, `4567/tcp` |

DB EC2는 인터넷에서 직접 접속하지 않는다. App/WAS EC2는 DB 노드가 아니라
HAProxy 또는 HAProxy 앞단 NLB의 3306(write), 3307(read)에 접근한다.

초기 검증 중 CloudFront prefix list 제한을 바로 적용하기 어렵다면 Web EC2의
`80/tcp`를 임시로 `0.0.0.0/0`에 열 수 있다. 최종 발표에서는 운영 권장 구조로
CloudFront origin-facing prefix list 또는 제한된 접근 제어를 설명한다.

Private Subnet의 DB/HAProxy/App EC2가 Docker Hub 또는 ECR에서 이미지를 Pull하려면
NAT Gateway, NAT Instance, 또는 사전 이미지 준비 방식이 필요하다.

## 4. ECR 저장소 준비

ECR은 EC2 이미지를 저장하는 곳이 아니라 Docker 컨테이너 이미지를 저장하는
곳이다. 이 프로젝트에서는 직접 만든 App 이미지 3개만 ECR에 저장한다.

```bash
aws ecr create-repository --repository-name inframodel-service-web
aws ecr create-repository --repository-name inframodel-admin-web
aws ecr create-repository --repository-name inframodel-was
```

DB Galera 이미지는 DB EC2에서 `Dockerfile.galera`로 빌드한다. Redis, Nginx,
HAProxy는 공식 이미지를 사용한다.

```text
mariadb:11.8.8
redis:7.4-alpine
nginx:1.26-alpine
haproxy:3.0-alpine
```

## 5. GitHub Actions 이미지 빌드와 Push

권장 방식은 GitHub Actions가 `aws-ecr` 브랜치 push 시 App 이미지를 빌드하고
ECR에 Push하는 것이다. `main` 브랜치 변동이 잦은 동안에는 AWS 배포 검증 전용
브랜치를 사용해 의도한 시점에만 이미지를 생성한다. 이 단계에서는 EC2 자동
재배포까지 수행하지 않는다. EC2 배포는 운영자가 이미지 태그를 확인한 뒤
`docker compose pull`과 `docker compose up -d`로 반영한다.

워크플로우:

```text
aws-ecr push
  -> GitHub Actions
  -> Docker image build
  -> ECR push
     - inframodel-service-web:aws-ecr-<short-sha>
     - inframodel-admin-web:aws-ecr-<short-sha>
     - inframodel-was:aws-ecr-<short-sha>
     - 각 이미지 stable 태그 갱신
```

GitHub Repository Secret:

| 이름 | 값 |
|---|---|
| `AWS_ROLE_TO_ASSUME` | ECR Push 권한이 있는 AWS IAM Role ARN |

GitHub Actions에서 AWS 장기 Access Key를 저장하지 않기 위해 OIDC 기반 Assume Role
방식을 사용한다. AWS IAM Role에는 GitHub OIDC Provider 신뢰 정책과 ECR Push 권한이
필요하다.

필요 ECR 권한 예시:

```text
ecr:GetAuthorizationToken
ecr:BatchCheckLayerAvailability
ecr:InitiateLayerUpload
ecr:UploadLayerPart
ecr:CompleteLayerUpload
ecr:PutImage
```

ECR Push 확인:

```bash
aws ecr list-images --repository-name inframodel-was
```

App EC2 배포 시에는 GitHub Actions 로그에 출력된 태그를 `.env`에 반영한다.

```dotenv
IMAGE_TAG=aws-ecr-a1b2c3d
```

이후 App EC2에서 실행한다.

```bash
docker compose --env-file .env pull
docker compose --env-file .env up -d
docker compose ps
```

`stable` 태그를 사용하면 최신 안정 버전을 쉽게 따라갈 수 있지만, 장애 분석과
롤백을 위해 실제 배포 기록에는 `aws-ecr-<short-sha>`처럼 커밋 기반 태그를
남기는 편이 좋다.

## 6. 수동 이미지 빌드와 Push

GitHub Actions를 사용하지 못하는 경우 로컬 또는 빌드 서버에서 수동으로 Push할 수
있다.

로컬 또는 빌드 서버에서 실행한다.

```bash
chmod +x deploy/aws/ecr-build-push.sh

ECR_REGISTRY='123456789012.dkr.ecr.ap-northeast-2.amazonaws.com' \
AWS_REGION='ap-northeast-2' \
IMAGE_TAG='v1.0' \
./deploy/aws/ecr-build-push.sh
```

확인:

```bash
aws ecr list-images --repository-name inframodel-was
```

`latest`만 쓰지 않고 `v1.0`, `v1.1`, `stable`처럼 버전 태그를 관리한다.

## 7. EC2 생성과 User Data

Web EC2, App/WAS EC2, DB EC2 모두 Ubuntu 24.04 기준으로 생성한다.

EC2 생성 시 User Data에 `user-data.sh` 내용을 입력하면 Docker Engine과 Docker
Compose Plugin 설치를 자동화할 수 있다.

작업 디렉터리는 모든 EC2에서 `/app`으로 통일한다. 기존 `~/inframodel-*`,
`/opt/inframodel` 경로는 사용하지 않는다.

EC2 접속 후 확인:

```bash
docker --version
docker compose version
systemctl status docker --no-pager
```

Web EC2와 App/WAS EC2에는 ECR Pull 권한이 있는 IAM Role을 연결한다.
SSM Parameter Store에서 설정을 읽는 인스턴스에는 다음 권한도 필요하다.

- `ssm:GetParameter`
- `s3:GetObject`
- SecureString을 고객 관리형 KMS 키로 암호화한 경우 해당 키의 `kms:Decrypt`

## 8. 배포 아티팩트 S3 업로드

GitHub Actions는 다음 파일을 S3에 업로드한다.

```text
deploy/aws/db/compose.galera.yaml -> s3://<bucket>/inframodel/prod/db/compose.galera.yaml
deploy/aws/db/compose.haproxy.yaml -> s3://<bucket>/inframodel/prod/db/compose.haproxy.yaml
deploy/aws/db/Dockerfile.galera -> s3://<bucket>/inframodel/prod/db/Dockerfile.galera
deploy/aws/db/docker-entrypoint-galera.sh -> s3://<bucket>/inframodel/prod/db/docker-entrypoint-galera.sh
deploy/aws/db/initdb-create-users.sh -> s3://<bucket>/inframodel/prod/db/initdb-create-users.sh
deploy/aws/db/config/vm/60-galera-common.cnf -> s3://<bucket>/inframodel/prod/db/config/vm/60-galera-common.cnf
deploy/aws/app/compose.yaml -> s3://<bucket>/inframodel/prod/app/compose.yaml
deploy/aws/web/compose.yaml -> s3://<bucket>/inframodel/prod/web/compose.yaml
deploy/aws/web/gateway/default.conf.template -> s3://<bucket>/inframodel/prod/web/gateway/default.conf.template
```

GitHub repository secrets:

- `AWS_ROLE_TO_ASSUME`: GitHub Actions OIDC로 AssumeRole 할 AWS IAM Role ARN
- `AWS_ARTIFACT_BUCKET`: compose와 Nginx template을 저장할 S3 버킷 이름

워크플로 파일은 `.github/workflows/deploy-aws-artifacts.yml`이다. `aws-ecr`
브랜치에 push하거나 수동 실행하면 S3 파일이 갱신된다.

## 9. DB EC2 배포

DB는 Galera MariaDB 3대와 HAProxy 2대 active/standby 구조로 배포한다.
DB 노드는 `deploy/aws/db/user-data-galera.sh`, HAProxy 노드는
`deploy/aws/db/user-data-haproxy.sh`를 사용한다.

`.env`는 직접 작성하지 않고 User Data가 SSM Parameter Store에서 값을 읽어
`/app/.env`로 생성한다. Galera secret 파일도 SSM SecureString에서 읽어
`/app/secrets/*.txt`로 생성한다.

SSM 파라미터 예시는 다음과 같다. 비밀번호성 값은 `SecureString`으로 저장한다.

```bash
aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/artifact-bucket \
  --type String \
  --value '<artifact-bucket>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/mariadb-database \
  --type String \
  --value integrated

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/mariadb-user \
  --type String \
  --value app

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/mariadb-password \
  --type SecureString \
  --value '<db-password>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/mariadb-root-password \
  --type SecureString \
  --value '<db-root-password>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/mariadb-sst-password \
  --type SecureString \
  --value '<hex-sst-password>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/galera-cluster-members \
  --type String \
  --value '<db1-private-ip>,<db2-private-ip>,<db3-private-ip>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/db1-host \
  --type String \
  --value '<db1-private-ip>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/db2-host \
  --type String \
  --value '<db2-private-ip>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/db3-host \
  --type String \
  --value '<db3-private-ip>'
```

SST 비밀번호는 `openssl rand -hex 24`처럼 hex 문자열로 만든다.

각 DB 노드 User Data에는 노드별 값을 지정해야 한다.

```bash
# db1
GALERA_NODE_NAME=db1
GALERA_SERVER_ID=1
GALERA_BOOTSTRAP=1

# db2
GALERA_NODE_NAME=db2
GALERA_SERVER_ID=2

# db3
GALERA_NODE_NAME=db3
GALERA_SERVER_ID=3
```

`GALERA_BOOTSTRAP=1`은 최초 db1 기동에만 사용한다. 클러스터가 만들어진 뒤에는
db1 Launch Template/User Data에서 `GALERA_BOOTSTRAP=0`으로 되돌린다.
이 값을 1로 둔 채 DB 인스턴스를 자동 교체하면 기존 클러스터와 분리된 새
클러스터가 만들어질 수 있으므로 DB ASG Instance Refresh 대상에 넣지 않는다.

HAProxy 노드는 다음처럼 이름만 다르게 지정한다.

```bash
# haproxy1
HAPROXY_NODE_NAME=haproxy1

# haproxy2
HAPROXY_NODE_NAME=haproxy2
```

HAProxy는 3306을 write endpoint, 3307을 read endpoint로 연다. WAS는 DB 노드가
아니라 HAProxy 또는 HAProxy 앞단 NLB를 바라봐야 한다.

부팅 후 확인:

```bash
cd /app
docker compose --env-file .env config
docker compose ps
```

보안 그룹 기준:

```text
WAS/App SG -> HAProxy SG TCP 3306, 3307
HAProxy SG -> DB SG TCP 3306
DB SG 내부 또는 DB node 간 TCP 4444, 4567
운영자 접근망 -> HAProxy SG TCP 8404, 필요 시 제한적으로 허용
```

## 10. App/WAS EC2 배포

App/WAS EC2는 FastAPI WAS와 Redis만 실행한다. Web 정적 프런트와 외부 Nginx
Gateway는 `deploy/aws/web`에서 실행한다.

App/WAS EC2는 User Data가 `/app`을 만들고 S3에서 compose 파일을 내려받는다.
`.env`는 직접 작성하지 않고 User Data가 SSM Parameter Store에서 값을 읽어
`/app/.env`로 생성한다.

SSM 파라미터 예시는 다음과 같다. 비밀번호성 값은 `SecureString`으로 저장한다.

```bash
aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/artifact-bucket \
  --type String \
  --value '<artifact-bucket>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/ecr-registry \
  --type String \
  --value 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/image-tag \
  --type String \
  --value v1.0

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/db-write-host \
  --type String \
  --value '<haproxy-or-nlb-endpoint>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/db-write-port \
  --type String \
  --value 3306

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/db-read-host \
  --type String \
  --value '<haproxy-or-nlb-endpoint>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/db-read-port \
  --type String \
  --value 3307

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/db-name \
  --type String \
  --value integrated

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/db-user \
  --type String \
  --value app

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/db-password \
  --type SecureString \
  --value '<db-password>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/jwt-secret \
  --type SecureString \
  --value '<jwt-secret-at-least-32-characters>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/admin-password \
  --type SecureString \
  --value '<admin-password>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/account-provider \
  --type String \
  --value local

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/cognito-region \
  --type String \
  --value ap-northeast-2

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/cognito-user-pool-id \
  --type String \
  --value ''

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/cognito-client-id \
  --type String \
  --value ''

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/cors-origins \
  --type String \
  --value 'https://www.example.com'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/kma-service-key \
  --type SecureString \
  --value '<kma-service-key>'
```

EC2 User Data에는 `deploy/aws/app/user-data.sh`를 사용한다. 기본 SSM prefix는
`/inframodel/prod/app`이며, 다른 prefix를 쓰려면 User Data 상단에서
`SSM_PREFIX`를 바꾼다.

부팅 후 확인:

```bash
cd /app
sudo test -f .env
docker compose --env-file .env ps
docker compose logs --tail=50 was
curl -i http://127.0.0.1:8000/
```

## 11. Web EC2 배포

Web EC2는 Nginx Gateway, service-web, admin-web만 실행한다. `/api/` 요청은
App/WAS EC2의 private IP와 8000 포트로 프록시한다.

Web EC2는 User Data가 `/app`을 만들고 S3에서 compose 파일과 Nginx template을
내려받는다. `.env`는 User Data가 SSM에서 읽어 생성한다.

SSM 파라미터 예시는 다음과 같다.

```bash
aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/web/artifact-bucket \
  --type String \
  --value '<artifact-bucket>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/web/ecr-registry \
  --type String \
  --value 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/web/image-tag \
  --type String \
  --value v1.0

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/web/was-upstream-host \
  --type String \
  --value 10.0.30.10

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/web/was-upstream-port \
  --type String \
  --value 8000
```

EC2 User Data에는 `deploy/aws/web/user-data.sh`를 사용한다.

부팅 후 확인:

```bash
cd /app
docker compose --env-file .env ps
curl -i http://127.0.0.1/health
curl -I http://127.0.0.1/
curl -I http://127.0.0.1/admin/
curl -s http://127.0.0.1/api/course-catalog | head
```

## 12. CloudFront, ACM, Route 53 검증

CloudFront를 외부 HTTPS 진입점으로 사용한다. Web EC2는 CloudFront origin으로
동작하고, 사용자는 Route 53 도메인으로 CloudFront에 접속한다.

ACM 인증서 주의사항:

- CloudFront에 연결할 ACM 인증서는 `us-east-1` 리전에서 발급한다.
- Route 53 DNS 검증을 사용하면 인증서 검증 레코드를 쉽게 추가할 수 있다.

CloudFront 설정 기준:

| 항목 | 값 |
|---|---|
| Origin domain | Web EC2 Public DNS 또는 Elastic IP 기반 도메인 |
| Origin protocol | HTTP |
| Viewer protocol policy | Redirect HTTP to HTTPS |
| Alternate domain name | 실제 서비스 도메인 |
| Custom SSL certificate | `us-east-1` ACM 인증서 |

Route 53에서는 App EC2가 아니라 CloudFront 배포로 Alias 레코드를 연결한다.

```text
도메인 A/AAAA Alias -> CloudFront Distribution
```

검증:

```bash
nslookup <도메인>
curl -I https://<도메인>/
curl -s https://<도메인>/api/course-catalog | head
```

발표에서는 “HTTPS 인증서는 ACM으로 관리하고, CloudFront가 외부 HTTPS 요청을
받아 Web EC2 origin으로 전달한다”고 설명한다.

## 13. 롤백 전략

새 버전 `v1.1` 배포 후 문제가 생기면 App EC2의 `.env`에서 `IMAGE_TAG`를 이전
정상 버전으로 되돌린다.

```dotenv
IMAGE_TAG=v1.0
```

이후 다시 배포한다.

```bash
docker compose --env-file .env pull
docker compose --env-file .env up -d
docker compose ps
docker compose logs --tail=50 was
```

발표에서는 “새 버전 장애 시 이전 이미지 태그로 되돌려 재배포할 수 있다”고
설명한다.

## 14. 운영 상태 확인

```bash
docker compose ps
docker stats --no-stream
free -h
df -h
uptime
docker compose logs --tail=50
```

AWS 콘솔에서는 EC2 Monitoring 탭에서 CPUUtilization, NetworkIn/Out,
StatusCheck를 확인한다.
