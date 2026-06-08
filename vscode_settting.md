# VScode 설정 방법

## 설치

[여기](https://code.visualstudio.com/)를 클릭하여 VScode 설치 파일을 다운로드합니다.

## Windows 기준 초기 설정

이번 팀 프로젝트는 Linux 3-Tier 서비스를 Docker Compose 구조로 전환하고 AWS 배포 가능성을 검증하는 프로젝트입니다. VS Code는 `compose.yaml`, `Dockerfile`, `nginx.conf`, `haproxy.cfg`, `.env.example`, User Data 스크립트 같은 설정 파일을 작성하고 확인하는 용도로 사용합니다.

### VS Code 설치 옵션

Windows 설치 파일을 실행할 때 아래 항목을 선택합니다.

- `Add to PATH`
- `Open with Code` 우클릭 메뉴 추가
- `Register Code as an editor for supported file types`

설치 후 VS Code를 실행하고 `File > Auto Save`는 팀원 취향에 따라 선택합니다. 실습 중에는 저장 누락을 줄이기 위해 켜두는 것을 권장합니다.

### 필수 확장 프로그램

확장 프로그램 탭에서 아래 확장을 설치합니다.

| 확장 프로그램 | Extension ID | 용도 |
| --- | --- | --- |
| Docker DX | `docker.docker` | Dockerfile, Compose 파일 작성 지원, 경고 표시, Compose outline 확인 |
| Remote - SSH | `ms-vscode-remote.remote-ssh` | AWS EC2 서버에 SSH로 접속해서 파일과 설정 확인 |

Docker Compose 파일은 별도 팀 컨벤션을 정하지 않았으므로 Docker DX 기본 설정을 우선 사용합니다.

<!-- ### 3. 권장 확장 프로그램

필수는 아니지만 작업 편의를 위해 아래 확장을 추가로 설치할 수 있습니다.

| 확장 프로그램 | Extension ID | 용도 |
| --- | --- | --- |
| YAML | `redhat.vscode-yaml` | 일반 YAML 파일 문법 확인과 포맷팅 보조 |
| AWS Toolkit | `amazonwebservices.aws-toolkit-vscode` | AWS 리소스 확인 보조 |
| GitLens | `eamodio.gitlens` | Git 변경 이력 확인 |

권장 확장은 팀 전체 필수는 아닙니다. 발표와 제출물 기준에서는 명령어 실행 결과와 캡처가 더 중요합니다. -->

### 4. VS Code 기본 설정

`Ctrl + Shift + P`를 누르고 `Preferences: Open User Settings (JSON)`을 선택한 뒤 아래 설정을 추가합니다.

```json
{
  "editor.formatOnSave": true,
  "editor.tabSize": 2,
  "editor.insertSpaces": true,
  "files.eol": "\n",
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "terminal.integrated.defaultProfile.windows": "PowerShell"
}
```

주의: 기존 설정 파일에 이미 `{ ... }`가 있으면 전체를 새로 붙여넣지 말고 필요한 항목만 추가합니다. JSON 파일은 마지막 항목 뒤에 쉼표를 붙이면 오류가 납니다.

### 5. 프로젝트 폴더 열기

VS Code에서 `File > Open Folder...`를 선택하고 팀 프로젝트 폴더를 엽니다. Docker Compose 관련 파일은 가능하면 아래 이름을 사용합니다.

- `compose.yaml`
- `Dockerfile`
- `.env.example`
- `nginx/default.conf`
- `haproxy/haproxy.cfg`
- `user-data.sh`

프로젝트 문서에서 코드와 설정 제출물이 중요하므로, 파일 이름과 위치를 팀원끼리 동일하게 맞춥니다.

### 6. Windows 터미널에서 기본 확인

VS Code 터미널을 열고 아래 명령어가 실행되는지 확인합니다.

```powershell
code --version
git --version
docker --version
docker compose version
ssh -V
```

Docker 명령어가 실행되지 않으면 Docker Desktop 실행 상태와 WSL 2 기반 엔진 설정을 먼저 확인합니다.

### 7. Compose 파일 작성 확인

`compose.yaml` 파일을 열었을 때 VS Code 오른쪽 Outline 영역에 services, networks, volumes 같은 항목이 보이면 Docker DX가 정상 동작하는 상태입니다.

작성 후에는 터미널에서 아래 명령어로 Compose 문법을 확인합니다.

```powershell
docker compose config
```

이 명령어가 오류 없이 전체 설정을 출력하면 Compose 파일 문법은 정상입니다.
