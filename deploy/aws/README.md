# AWS EC2/ECR/CloudFront/Route 53 배포 검증

이 디렉터리는 VMware에서 검증한 Docker Compose 구조를 AWS에서도 실행 가능한지
확인하기 위한 배포 산출물이다.

AWS 단계에서는 App EC2와 DB EC2를 분리한다. App EC2는 Public Subnet에서
CloudFront의 origin 역할을 하고, DB EC2는 Private Subnet에서 App EC2의 요청만
받는다. 외부 HTTPS 접속은 CloudFront와 ACM 인증서로 처리한다.

## 1. 목표 구조

```text
Route 53
  -> CloudFront + ACM
  -> Public Subnet
     -> App EC2 origin:80
        -> gateway
           /        -> service-web
           /admin/  -> admin-web
           /api/    -> was
                       -> Private Subnet DB EC2:3306
        -> redis

Private Subnet
  -> DB EC2
     -> mariadb
```

## 2. 디렉터리 구성

| 경로 | 용도 |
|---|---|
| `app/compose.yaml` | Public Subnet의 App EC2에서 실행 |
| `app/.env.example` | App EC2 환경변수 예시 |
| `app/gateway/default.conf.template` | App EC2 gateway Nginx 설정 |
| `db/compose.yaml` | Private Subnet의 DB EC2에서 실행 |
| `db/.env.example` | DB EC2 환경변수 예시 |
| `user-data.sh` | EC2 초기 Docker 설치 자동화 |
| `ecr-build-push.sh` | App 이미지를 ECR에 버전 태그로 Push |
| `.github/workflows/ecr-build.yml` | `aws-ecr` 브랜치 push 시 App 이미지를 ECR에 자동 Push |

## 3. VPC와 Security Group

권장 네트워크 구성:

| 리소스 | 위치 | 외부 접근 |
|---|---|---|
| App EC2 | Public Subnet | CloudFront origin 요청, SSH 22 제한 허용 |
| DB EC2 | Private Subnet | Public IP 없음 |

Security Group 예시:

| 대상 | Inbound |
|---|---|
| App EC2 SG | `80/tcp` from CloudFront origin-facing prefix list, `22/tcp` from 관리자 IP |
| DB EC2 SG | `3306/tcp` from App EC2 Security Group |

DB EC2는 인터넷에서 직접 접속하지 않는다. App EC2의 WAS 컨테이너만 DB EC2의
private IP로 MariaDB에 접근한다.

초기 검증 중 CloudFront prefix list 제한을 바로 적용하기 어렵다면 App EC2의
`80/tcp`를 임시로 `0.0.0.0/0`에 열 수 있다. 최종 발표에서는 운영 권장 구조로
CloudFront origin-facing prefix list 또는 제한된 접근 제어를 설명한다.

Private Subnet의 DB EC2가 Docker Hub에서 `mariadb:11.4` 이미지를 Pull하려면 NAT
Gateway, NAT Instance, 또는 사전 이미지 준비 방식이 필요하다. 비용을 줄이는
실습 환경에서는 DB EC2를 Public Subnet에 두되 Public IP를 부여하지 않고 Security
Group으로 3306 접근을 App EC2 SG로 제한하는 방식도 선택할 수 있다.

## 4. ECR 저장소 준비

ECR은 EC2 이미지를 저장하는 곳이 아니라 Docker 컨테이너 이미지를 저장하는
곳이다. 이 프로젝트에서는 직접 만든 App 이미지 3개만 ECR에 저장한다.

```bash
aws ecr create-repository --repository-name inframodel-service-web
aws ecr create-repository --repository-name inframodel-admin-web
aws ecr create-repository --repository-name inframodel-was
```

DB와 Redis는 직접 만든 이미지가 아니므로 공식 이미지를 사용한다.

```text
mariadb:11.4
redis:7.4-alpine
nginx:1.26-alpine
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
deploy/aws/db/compose.yaml -> s3://<bucket>/inframodel/prod/db/compose.yaml
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

DB EC2는 User Data가 `/app`을 만들고 S3에서 compose 파일을 내려받는다.

`.env`는 직접 작성하지 않고 User Data가 SSM Parameter Store에서 값을 읽어
`/app/.env`로 생성한다.

SSM 파라미터 예시는 다음과 같다. 비밀번호성 값은 `SecureString`으로 저장한다.

```bash
aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/artifact-bucket \
  --type String \
  --value '<artifact-bucket>'

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/db/db-bind-ip \
  --type String \
  --value 0.0.0.0

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
```

EC2 User Data에는 `deploy/aws/db/user-data.sh`를 사용한다. 기본 SSM prefix는
`/inframodel/prod/db`이다.

부팅 후 확인:

```bash
cd /app
docker compose --env-file .env config
docker compose ps
```

DB EC2 private IP를 기록한다. 예:

```text
10.0.20.10
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
  --name /inframodel/prod/app/db-host \
  --type String \
  --value 10.0.20.10

aws ssm put-parameter --region ap-northeast-2 --overwrite \
  --name /inframodel/prod/app/db-port \
  --type String \
  --value 3306

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
