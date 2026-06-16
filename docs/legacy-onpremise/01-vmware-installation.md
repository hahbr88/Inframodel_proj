# VMware 환경 구성

## 개요

본 문서는 레거시 온프레미스 환경 구축을 위한 VMware 가상머신 생성 및 Ubuntu Server 설치 절차를 정의한다.

모든 팀원은 본 문서를 기준으로 동일한 환경을 구축해야 한다.

---

# 구축 대상 서버

| 서버명        | 역할              |
| ------------- | ----------------- |
| legacy-ops-01 | 운영 서버         |
| legacy-web-01 | 웹 서버           |
| legacy-app-01 | 애플리케이션 서버 |
| legacy-db-01  | 데이터베이스 서버 |

---

# 사전 준비

다음 파일을 준비한다.

| 항목    | 값                                   |
| ------- | ------------------------------------ |
| VMware  | VMware Workstation Pro               |
| OS      | Ubuntu Server 24.04.4 LTS            |
| ISO     | ubuntu-24.04.4-live-server-amd64.iso |
| Network | VMnet8 (NAT)                         |

---

# VMware 저장 폴더 생성

가상머신은 아래 구조로 관리한다.

```text
VMware/
 └─ Legacy-OnPremise/
      ├─ legacy-ops-01
      ├─ legacy-web-01
      ├─ legacy-app-01
      └─ legacy-db-01
```

---

# 가상머신 생성

VMware Workstation Pro 실행

상단 메뉴 선택

```text
File
 └─ New Virtual Machine
```

---

# Guest OS 설치

### Installer disc image file (ISO)

Ubuntu ISO 선택

```text
ubuntu-24.04.4-live-server-amd64.iso
```

Next 클릭

---

# Virtual Machine Name 설정

## legacy-ops-01

```text
Virtual Machine Name
legacy-ops-01
```

Location

```text
VMware\Legacy-OnPremise\legacy-ops-01
```

---

## legacy-web-01

```text
Virtual Machine Name
legacy-web-01
```

Location

```text
VMware\Legacy-OnPremise\legacy-web-01
```

---

## legacy-app-01

```text
Virtual Machine Name
legacy-app-01
```

Location

```text
VMware\Legacy-OnPremise\legacy-app-01
```

---

## legacy-db-01

```text
Virtual Machine Name
legacy-db-01
```

Location

```text
VMware\Legacy-OnPremise\legacy-db-01
```

---

# 서버 자원 설정

## legacy-ops-01

| 항목    | 값     |
| ------- | ------ |
| CPU     | 1 Core |
| Memory  | 2 GB   |
| Storage | 10 GB  |

---

## legacy-web-01

| 항목    | 값     |
| ------- | ------ |
| CPU     | 1 Core |
| Memory  | 2 GB   |
| Storage | 20 GB  |

---

## legacy-app-01

| 항목    | 값     |
| ------- | ------ |
| CPU     | 2 Core |
| Memory  | 4 GB   |
| Storage | 30 GB  |

---

## legacy-db-01

| 항목    | 값     |
| ------- | ------ |
| CPU     | 2 Core |
| Memory  | 4 GB   |
| Storage | 60 GB  |

---

# 네트워크 설정

각 서버 VM 선택

```text
VM
 └─ Settings
      └─ Network Adapter
```

설정

```text
NAT
(VMnet8)
```

적용 후 저장

---

# Ubuntu 설치 시작

가상머신 전원 켜기

```text
Power On This Virtual Machine
```

---

# Language 선택

```text
English
```

선택

---

# Keyboard Configuration

```text
English (US)
```

선택

---

# Ubuntu Server Installer

기본값 선택

```text
Ubuntu Server
```

---

# Network Configuration

기본값 유지

네트워크 상세 설정은

```text
02-network-configuration.md
```

에서 진행한다.

---

# Proxy Configuration

기본값 유지

```text
Blank
```

---

# Ubuntu Archive Mirror

기본값 유지

Continue

---

# Storage Configuration

기본값 선택

```text
Use an entire disk
```

---

# Profile Setup

Hostname 입력

## legacy-ops-01

```text
legacy-ops-01
```

## legacy-web-01

```text
legacy-web-01
```

## legacy-app-01

```text
legacy-app-01
```

## legacy-db-01

```text
legacy-db-01
```

---

관리자 계정 생성

```text
Your name
admin

Server name
각 서버 Hostname

Username
admin

Password
admin1234

Confirm Password
admin1234
```

---

# SSH 설정

SSH 설정 화면에서 반드시 체크

```text
[✔] Install OpenSSH Server
```

Next 진행

---

# 설치 완료

설치 완료 후

```text
Reboot Now
```

선택

---

# 최초 로그인

로그인

```text
Username
admin

Password
admin1234
```

---

# 시스템 업데이트

패키지 목록 업데이트

```bash
sudo apt update
```

시스템 업데이트

```bash
sudo apt upgrade -y
```

재부팅

```bash
sudo reboot
```

---

# 운영체제 확인

```bash
cat /etc/os-release
```

예상 결과

```text
Ubuntu 24.04.4 LTS
```

---

# Hostname 확인

```bash
hostnamectl
```

설정한 Hostname이 표시되어야 한다.

---

# 계정 확인

```bash
whoami
```

예상 결과

```text
admin
```

---

# sudo 권한 확인

```bash
sudo -l
```

sudo 권한이 표시되어야 한다.

---

# 네트워크 확인

```bash
ip addr
```

VMnet8 네트워크가 확인되어야 한다.

---

# SSH 서비스 확인

```bash
systemctl status ssh
```

예상 결과

```text
Active: active (running)
```

---

# Snapshot 생성

초기 설치 완료 후 Snapshot 생성

```text
VM
 └─ Snapshot
      └─ Take Snapshot
```

설정

```text
Name
OS-Install
```

---

# 구축 완료 기준

다음 항목을 모두 만족해야 한다.

- 서버 4대 생성 완료
- Ubuntu Server 24.04.4 LTS 설치 완료
- VMnet8 적용 완료
- Hostname 설정 완료
- admin 계정 생성 완료
- OpenSSH Server 설치 완료
- 시스템 업데이트 완료
- SSH 서비스 실행 확인
- Snapshot 생성 완료

---

# 다음 단계

다음 문서 진행

```text
02-network-configuration.md
```
