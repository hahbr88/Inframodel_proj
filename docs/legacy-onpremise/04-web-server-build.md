# 웹 서버 구축

## 개요

본 문서는 레거시 온프레미스 환경의 웹 서버(legacy-web-01) 구축 절차를 정의한다.

웹 서버는 사용자의 웹 요청을 최초로 수신하는 서버이며 React 웹 서비스 제공 역할을 수행한다.

본 단계에서는 Nginx 설치 및 웹 서비스 동작 환경을 구성한다.

애플리케이션 서버(FastAPI)와의 Reverse Proxy 구성은 WAS 서버 구축 완료 후 진행한다.

---

# 서버 정보

| 항목     | 설정값                     |
| -------- | -------------------------- |
| 서버명   | legacy-web-01              |
| 역할     | Web Server / Reverse Proxy |
| 운영체제 | Ubuntu Server 24.04.4 LTS  |
| CPU      | 1 Core                     |
| Memory   | 2 GB                       |
| Storage  | 20 GB                      |
| IP 주소  | 192.168.100.10/24          |

---

# 서버 상태 확인

서버에 접속 후 서버 정보를 확인한다.

```bash
hostnamectl
```

확인 결과 서버명이 아래와 같이 표시되어야 한다.

```text
legacy-web-01
```

IP 주소를 확인한다.

```bash
ip addr
```

---

# 패키지 업데이트

패키지 저장소 정보를 최신 상태로 갱신한다.

```bash
sudo apt update
```

설치된 패키지를 최신 상태로 업데이트한다.

```bash
sudo apt upgrade -y
```

---

# Nginx 설치

웹 서비스를 제공하기 위해 Nginx를 설치한다.

```bash
sudo apt install nginx -y
```

설치 완료 후 서비스 상태를 확인한다.

```bash
sudo systemctl status nginx
```

서비스가 active (running) 상태로 표시되어야 한다.

---

# Nginx 자동 시작 확인

서버 재부팅 후에도 자동으로 실행되는지 확인한다.

```bash
sudo systemctl is-enabled nginx
```

확인 결과

```text
enabled
```

로 표시되어야 한다.

---

# 서비스 포트 확인

Nginx가 정상적으로 포트를 수신하고 있는지 확인한다.

```bash
ss -tulpen | grep ':80'
```

---

# 웹 서비스 확인

브라우저에서 아래 주소로 접속한다.

```text
http://192.168.100.10
```

Nginx 기본 페이지가 표시되어야 한다.

---

# React 서비스 배포

React 서비스는 웹 서버에서 제공한다.

React 프로젝트의 실제 배포 방식은 프로젝트 산출물 기준에 따라 진행한다.

배포 완료 후 웹 브라우저에서 React 화면이 정상적으로 표시되어야 한다.

---

# Reverse Proxy 구성 안내

본 환경에서 웹 서버는 최종적으로 Reverse Proxy 역할을 수행한다.

서비스 구조는 아래와 같다.

```text
Internet
    │
    ▼
legacy-web-01
(Nginx)
    │
    ▼
legacy-app-01
(FastAPI)
```

애플리케이션 서버 구축 완료 후 Nginx Reverse Proxy 설정을 진행한다.

해당 설정 및 검증은 WAS 서버 구축 이후 단계에서 수행한다.

---

# 점검 항목

| 점검 항목                 | 확인 |
| ------------------------- | ---- |
| 서버 접속 확인            | □    |
| 서버명 확인               | □    |
| IP 주소 확인              | □    |
| 패키지 업데이트 완료      | □    |
| Nginx 설치 완료           | □    |
| Nginx 서비스 실행         | □    |
| Nginx 자동 시작 설정 확인 | □    |
| 80 포트 수신 확인         | □    |
| 웹 페이지 접속 확인       | □    |

---

# 구축 완료 기준

다음 항목을 모두 만족하면 웹 서버 구축이 완료된 것으로 판단한다.

- Nginx 설치 완료
- Nginx 서비스 정상 동작
- Nginx 자동 시작 설정 확인
- 웹 페이지 정상 접속
- 80 포트 수신 확인
- React 서비스 배포 준비 완료

---

# 다음 단계

웹 서버 구축이 완료되면 아래 문서를 진행한다.

- 05-was-server-build.md
