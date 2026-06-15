# Inframodel_proj

이번 팀 프로젝트는 Linux 3-Tier 서비스를 Docker Compose 구조로 전환하고 AWS 배포 가능성을 검증하는 프로젝트입니다.

## VScode 다운로드 및 환경설정

[여기](vscode_settting.md)를 클릭해서 확인

---

## 레포지토리 클론

레포 클론할 VM에 git 설치

```bash
sudo apt update
sudo apt install git -y
```

설치확인

```bash
git --version
```

홈디렉토리(~) 에서 아래와 같이 명령어 입력

```bash
mkdir docker
cd docker
git clone https://github.com/hahbr88/Inframodel_proj.git
```

---

## 레포지토리 관리 (CLI)

프로젝트 디렉토리에서

```bash
git fetch
```

원격 저장소의 최신 커밋이 있는지 확인

```bash
git status
git log --oneline --decorate --graph -5
```

현재 브랜치의 최신 내용을 반영

```bash
git pull origin main
```

<!-- 만약 기본 브랜치가 `master` 인 저장소라면 아래처럼 확인 후 맞는 브랜치명으로 pull

```bash
git branch
git branch -r
``` -->

로컬에서 수정한 파일이 없고 단순히 최신화만 할 때는 보통 아래 순서로 진행

```bash
cd ~/docker/Inframodel_proj
git fetch
git pull origin main
```

**(중요!) 로컬 변경 사항이 있을 때는 바로 `pull` 하지 말고 먼저 상태 확인**

```bash
git status
```

`modified` 파일이 보이면 아래 둘 중 하나로 정리 후 진행

1. 아직 커밋할 작업이면 먼저 커밋

```bash
git add .
git commit -m "작업 내용 정리"
git pull origin main
```

2. 잠깐 보관만 하고 최신화할 거면 stash 사용

```bash
git stash
git pull origin main
git stash pop
```

현재 연결된 원격 저장소 확인

```bash
git remote -v
```

전체 흐름 요약

```bash
cd ~/docker/Inframodel_proj
git status
git fetch
git pull origin main
```

---

## GitHub 협업 규칙

- `main` 브랜치는 최종본이며 직접 `push` 하지 않습니다.
- 작업 시작 전 반드시 새 브랜치를 만듭니다.
- 작업이 끝나면 `Pull Request(PR)` 를 생성합니다.
- 최소 1명의 승인 후 병합합니다.
- 병합 방식은 항상 `Squash merge` 를 사용합니다.

### 브랜치 이름 규칙

- 문서 작업: `docs/작업명`
- 기능 작업: `feature/기능명`
- 수정 작업: `fix/수정명`

예시

```text
docs/infra-spec
docs/network-diagram
feature/docker-compose
fix/readme-typo
```

---

<!-- ## GitHub 권장 설정

GitHub 저장소 설정은 아래 기준으로 맞추는 것을 권장합니다.

```text
Require a pull request before merging: 체크
Required approvals: 1
Dismiss stale approvals: 체크
Require conversation resolution before merging: 체크
Block force pushes: 체크
Require status checks to pass: 일단 해제
Allowed merge methods: Squash만 허용
``` -->

**핵심은 아래 흐름을 지키는 것입니다.**

> 브랜치 생성 -> 작업 -> PR 생성 -> 승인 1개 -> Squash merge

---

## 팀원 작업 순서

### 1. 작업 전 최신화

```bash
cd ~/docker/Inframodel_proj
git checkout main
git pull origin main
```

### 2. 새 브랜치 생성

예시: 문서 작업을 시작하는 경우

```bash
git checkout -b docs/network-config
```

### 3. 작업 후 커밋

```bash
git add .
git commit -m "docs: add network configuration"
```

### 4. GitHub에 브랜치 올리기

```bash
git push origin docs/network-config
```

### 5. GitHub에서 PR 생성

GitHub 화면에서 아래 순서로 진행합니다.

```text
Compare & pull request 클릭
-> 제목 작성
-> Create pull request 클릭
```

### 6. 팀원 승인

다른 팀원 1명이 아래 순서로 확인합니다.

```text
Files changed 확인
-> 문제 없으면 Approve
```

### 7. 병합

병합은 반드시 아래 방식으로 진행합니다.

```text
Squash and merge
```

---

## 초반 운영 방식

팀원들이 GitHub에 아직 익숙하지 않으니, 초반에는 역할을 아래처럼 나눠서 진행하겠습니다.

- 팀원: 브랜치 생성, 작업, 커밋, `push`, PR 생성
- 팀장: PR 확인, 충돌 확인, 승인 확인, `Squash merge`

---

# Legacy On-Premise Infrastructure

레거시 3-Tier 기반 온프레미스 인프라 구축 및 운영 문서입니다.

## 운영 관리대장

- [Legacy Infrastructure Management](docs/legacy-onpremise/legacy-infra-management.xlsx)

## 구축 문서

- [01 VMware 환경 구성](docs/legacy-onpremise/01-vmware-installation.md)
- [02 네트워크 구성](docs/legacy-onpremise/02-network-configuration.md)
- [03 운영 서버 구축](docs/legacy-onpremise/03-ops-server-build.md)
- [04 웹 서버 구축](docs/legacy-onpremise/04-web-server-build.md)
- [05 WAS 서버 구축](docs/legacy-onpremise/05-was-server-build.md)
- [06 DB 서버 구축](docs/legacy-onpremise/06-db-server-build.md)
- [07 DNS 서버 구축](docs/legacy-onpremise/07-dns-server-build.md)
- [08 NTP 서버 구축](docs/legacy-onpremise/08-ntp-server-build.md)
- [09 DB 백업 구성](docs/legacy-onpremise/09-database-backup.md)
- [10 VPN 서버 구축](docs/legacy-onpremise/10-vpn-server-build.md)
- [11 최종 검증](docs/legacy-onpremise/11-system-validation.md)

---

### 문서 버젼 관리

| 작성일   | 작성자 | 버젼 |
| -------- | ------ | ---- |
| 20260608 | 하병노 | 1.0  |
| 20260609 | 하병노 | 1.01 |
| 20260615 | 김수현 | 1.02 |
