# 네트워크 구성

## 개요

본 문서는 레거시 온프레미스 환경의 네트워크 구성 절차를 정의한다.

모든 서버는 VMware VMnet8(NAT) 환경에서 고정 IP를 사용한다.

본 단계에서는 서버별 고정 IP 설정, Gateway 설정 및 서버 간 통신 검증을 수행한다.

---

# 네트워크 정보

| 항목           | 설정값                            |
| -------------- | --------------------------------- |
| Network        | 192.168.100.0/24                  |
| Gateway        | 192.168.100.2                     |
| VMware Network | VMnet8                            |
| Network Type   | NAT                               |
| DHCP Range     | 192.168.100.128 ~ 192.168.100.254 |
| IP 방식        | Static IP                         |

---

# 관리자 계정

01 VMware Installation 문서에서 생성한 공통 관리자 계정을 사용한다.

| 항목     | 값        |
| -------- | --------- |
| Username | admin     |
| Password | admin1234 |

---

# 서버별 IP 계획

| 서버명        | IP 주소           |
| ------------- | ----------------- |
| legacy-ops-01 | 192.168.100.5/24  |
| legacy-web-01 | 192.168.100.10/24 |
| legacy-app-01 | 192.168.100.20/24 |
| legacy-db-01  | 192.168.100.30/24 |

---

# 작업 대상 서버 로그인

각 서버에 로그인한다.

```text
legacy-ops-01
legacy-web-01
legacy-app-01
legacy-db-01
```

로그인 계정

```text
Username : admin
Password : admin1234
```

현재 로그인 계정을 확인한다.

```bash
whoami
```

예상 결과

```text
admin
```

---

# 현재 네트워크 인터페이스 확인

각 서버에서 네트워크 인터페이스 이름을 확인한다.

```bash
ip addr
```

예시

```text
ens33
```

또는

```text
ens160
```

또는

```text
ens192
```

반드시 실제 확인된 인터페이스명을 기록한다.

예시

```text
legacy-ops-01 : ens33
legacy-web-01 : ens33
legacy-app-01 : ens33
legacy-db-01 : ens33
```

환경에 따라 인터페이스명이 다를 수 있다.

---

# Netplan 설정 파일 확인

Netplan 설정 파일명을 확인한다.

```bash
ls /etc/netplan
```

예시

```text
50-cloud-init.yaml
```

또는

```text
00-installer-config.yaml
```

실제 확인된 파일명을 기록한다.

예시

```text
50-cloud-init.yaml
```

이후 모든 명령어는 실제 확인된 파일명을 사용한다.

---

# Netplan 설정 파일 백업

설정 변경 전 백업을 생성한다.

예시

```bash
sudo cp \
/etc/netplan/50-cloud-init.yaml \
/etc/netplan/50-cloud-init.yaml.bak
```

파일명이 다른 경우 실제 파일명으로 변경한다.

백업 파일을 확인한다.

```bash
ls -al /etc/netplan
```

---

# legacy-ops-01 고정 IP 설정

설정 파일을 수정한다.

예시

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

인터페이스명이 `ens33`인 경우 아래 내용을 입력한다.

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: false
      addresses:
        - 192.168.100.5/24
      routes:
        - to: default
          via: 192.168.100.2
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

주의

```text
ens33 부분은 실제 확인한 인터페이스명 사용
```

---

# legacy-web-01 고정 IP 설정

설정 파일을 수정한다.

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

인터페이스명이 `ens33`인 경우 아래 내용을 입력한다.

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: false
      addresses:
        - 192.168.100.10/24
      routes:
        - to: default
          via: 192.168.100.2
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

---

# legacy-app-01 고정 IP 설정

설정 파일을 수정한다.

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

인터페이스명이 `ens33`인 경우 아래 내용을 입력한다.

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: false
      addresses:
        - 192.168.100.20/24
      routes:
        - to: default
          via: 192.168.100.2
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

---

# legacy-db-01 고정 IP 설정

설정 파일을 수정한다.

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

인터페이스명이 `ens33`인 경우 아래 내용을 입력한다.

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: false
      addresses:
        - 192.168.100.30/24
      routes:
        - to: default
          via: 192.168.100.2
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

---

# 설정 저장

Nano Editor 기준

```text
Ctrl + O
Enter
Ctrl + X
```

---

# Netplan 설정 문법 확인

설정 문법을 확인한다.

```bash
sudo netplan generate
```

오류가 없어야 한다.

---

# Netplan 적용

설정을 적용한다.

```bash
sudo netplan apply
```

네트워크가 재시작된다.

---

# IP 주소 확인

현재 IP를 확인한다.

```bash
ip addr
```

확인 기준

| 서버명        | 확인 IP        |
| ------------- | -------------- |
| legacy-ops-01 | 192.168.100.5  |
| legacy-web-01 | 192.168.100.10 |
| legacy-app-01 | 192.168.100.20 |
| legacy-db-01  | 192.168.100.30 |

---

# Gateway 확인

라우팅 정보를 확인한다.

```bash
ip route
```

예상 결과

```text
default via 192.168.100.2
```

---

# 인터넷 연결 확인

외부 통신을 확인한다.

```bash
ping -c 4 8.8.8.8
```

정상적으로 응답해야 한다.

---

# DNS 이름 해석 확인

도메인 이름 해석을 확인한다.

```bash
ping -c 4 google.com
```

정상적으로 응답해야 한다.

---

# 서버 간 통신 확인

## legacy-ops-01

```bash
ping -c 4 192.168.100.10
```

```bash
ping -c 4 192.168.100.20
```

```bash
ping -c 4 192.168.100.30
```

---

## legacy-web-01

```bash
ping -c 4 192.168.100.20
```

---

## legacy-app-01

```bash
ping -c 4 192.168.100.30
```

---

# DHCP 충돌 확인

현재 VMware DHCP 범위를 확인한다.

```text
192.168.100.128 ~ 192.168.100.254
```

현재 사용 중인 고정 IP는 아래 범위를 사용한다.

```text
192.168.100.5
192.168.100.10
192.168.100.20
192.168.100.30
```

DHCP 범위 밖이므로 충돌하지 않는다.

---

# DNS 서버 변경 예정 안내

현재는 외부 DNS를 사용한다.

```text
8.8.8.8
1.1.1.1
```

07 DNS Server Build 완료 후 아래 DNS 서버로 변경한다.

```text
192.168.100.5
```

DNS 변경 작업은 07 DNS Server Build 문서에서 수행한다.

---

# Snapshot 생성

네트워크 설정 완료 후 Snapshot을 생성한다.

VMware 메뉴

```text
VM
 └─ Snapshot
      └─ Take Snapshot
```

설정

```text
Name
02-Network-Complete
```

---

# 구축 완료 기준

다음 항목을 모두 만족해야 한다.

- admin 계정 로그인 확인
- 고정 IP 설정 완료
- Gateway 설정 완료
- Netplan 적용 완료
- 서버별 IP 확인 완료
- 인터넷 연결 확인 완료
- DNS 이름 해석 확인 완료
- 서버 간 Ping 통신 성공
- DHCP 충돌 없음 확인
- Snapshot 생성 완료

---

# 다음 단계

```text
03-ops-server-build.md
```
