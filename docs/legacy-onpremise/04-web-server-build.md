# 웹 서버 구축

## 개요

본 문서는 레거시 온프레미스 환경의 웹 서버(`legacy-web-01`) 구축 절차를 정의한다.

웹 서버는 사용자의 HTTP 요청을 최초로 수신하는 서버이며 Nginx Reverse Proxy를 통해 애플리케이션 서버(`legacy-app-01`)로 요청을 전달한다.

본 문서에서는 Nginx 설치, 웹 서버 동작 확인, Reverse Proxy 설정까지 진행한다.

실제 Reverse Proxy 연동 검증은 `05-was-server-build.md` 문서에서 수행한다.

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

# 관리자 계정

| 항목     | 값        |
| -------- | --------- |
| Username | admin     |
| Password | admin1234 |

---

# 사전 조건

```text
01 VMware Installation
02 Network Configuration
```

완료 상태여야 한다.

---

# 서버 상태 확인

현재 로그인 계정을 확인한다.

```bash
whoami
```

예상 결과

```text
admin
```

서버명을 확인한다.

```bash
hostnamectl
```

예상 결과

```text
Static hostname: legacy-web-01
```

IP 주소를 확인한다.

```bash
ip addr
```

예상 결과

```text
192.168.100.10/24
```

운영체제 버전을 확인한다.

```bash
lsb_release -a
```

---

# 패키지 업데이트

```bash
sudo apt update
```

```bash
sudo apt upgrade -y
```

---

# 운영 도구 설치

```bash
sudo apt install -y \
vim \
curl \
wget \
net-tools \
htop \
tree \
unzip
```

---

# Nginx 설치

```bash
sudo apt install nginx -y
```

버전을 확인한다.

```bash
nginx -v
```

---

# Nginx 서비스 확인

```bash
sudo systemctl start nginx
```

```bash
sudo systemctl enable nginx
```

```bash
sudo systemctl status nginx
```

예상 결과

```text
active (running)
```

---

# 80 포트 확인

```bash
sudo ss -tulnp | grep ':80'
```

예상 결과

```text
0.0.0.0:80
```

---

# 방화벽 확인

현재 상태 확인

```bash
sudo ufw status
```

예상 결과

```text
Status: active
```

HTTP 허용

```bash
sudo ufw allow 80/tcp
```

HTTPS 허용

```bash
sudo ufw allow 443/tcp
```

확인

```bash
sudo ufw status
```

---

# Nginx 기본 페이지 확인

서버 내부

```bash
curl http://localhost
```

관리 PC

```bash
curl http://192.168.100.10
```

브라우저

```text
http://192.168.100.10
```

Nginx 기본 페이지가 표시되어야 한다.

---

# 기본 웹 파일 백업

```bash
ls -al /var/www/html
```

```bash
sudo cp \
/var/www/html/index.nginx-debian.html \
/var/www/html/index.nginx-debian.html.bak
```

---

# Reverse Proxy 설정

설정 파일 백업

```bash
sudo cp \
/etc/nginx/sites-available/default \
/etc/nginx/sites-available/default.bak
```

설정 수정

```bash
sudo vi /etc/nginx/sites-available/default
```

내용

```nginx
server {

    listen 80;

    server_name _;

    location / {

        proxy_pass http://192.168.100.20:8000;

        proxy_set_header Host $host;

        proxy_set_header X-Real-IP $remote_addr;

        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_set_header X-Forwarded-Proto $scheme;

    }

}
```

---

# 설정 검증

문법 확인

```bash
sudo nginx -t
```

예상 결과

```text
syntax is ok
test is successful
```

설정 적용

```bash
sudo systemctl restart nginx
```

상태 확인

```bash
sudo systemctl status nginx
```

설정 확인

```bash
sudo cat /etc/nginx/sites-available/default
```

---

# Reverse Proxy 검증 안내

현재 단계에서는 WAS 서버가 아직 실행되지 않은 상태일 수 있다.

```text
192.168.100.20:8000
```

으로 연결이 되지 않으면 아래 오류가 발생할 수 있다.

```text
502 Bad Gateway
```

이는 정상이다.

실제 Reverse Proxy 연동 검증은 `05-was-server-build.md` 문서에서 수행한다.

---

# SSH 접속 검증

관리 PC에서 접속한다.

```bash
ssh admin@192.168.100.10
```

정상 로그인되어야 한다.

---

# 재부팅 검증

```bash
sudo reboot
```

재접속 후 확인

```bash
sudo systemctl status nginx
```

```bash
sudo ss -tulnp | grep ':80'
```

```bash
sudo nginx -t
```

---

# Snapshot 생성

VMware 메뉴

```text
VM
 └─ Snapshot
      └─ Take Snapshot
```

설정

```text
Name
04-Web-Complete
```

---

# 구축 완료 기준

- admin 계정 로그인 가능
- Nginx 설치 완료
- Nginx 서비스 정상 동작
- 80 포트 수신 확인
- HTTP 접속 가능
- Reverse Proxy 설정 완료
- Nginx 설정 검증 완료
- SSH 접속 검증 완료
- 재부팅 후 정상 동작
- Snapshot 생성 완료

---

# 다음 단계

```text
05 WAS Server Build
```
