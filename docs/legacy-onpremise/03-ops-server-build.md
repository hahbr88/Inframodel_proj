# 운영 서버 구축

## 개요

본 문서는 레거시 온프레미스 환경의 운영 서버(legacy-ops-01)를 구축하기 위한 가이드이다.

운영 서버는 인프라 운영에 필요한 공통 서비스를 제공하는 서버로 사용한다.

본 단계에서는 VMware 가상머신 생성, Ubuntu Server 설치, 서버명 설정 및 네트워크 설정까지 진행한다.

DNS, NTP, VPN 서비스 구성은 이후 문서에서 진행한다.

---

# 서버 정보

| 항목       | 설정값                    |
| ---------- | ------------------------- |
| 서버명     | legacy-ops-01             |
| 역할       | 운영 서버                 |
| OS         | Ubuntu Server 24.04.4 LTS |
| CPU        | 1 Core                    |
| Memory     | 2 GB                      |
| Storage    | 10 GB                     |
| Network    | NAT (VMnet8)              |
| IP Address | 192.168.100.5/24          |
| Gateway    | 192.168.100.1             |

---

# VMware 가상머신 생성

VMware Workstation에서 새로운 가상머신을 생성한다.

## 생성 기준

| 항목            | 값            |
| --------------- | ------------- |
| Guest OS        | Linux         |
| Version         | Ubuntu 64-bit |
| Firmware        | BIOS          |
| CPU             | 1 Core        |
| Memory          | 2048 MB       |
| Disk Size       | 10 GB         |
| Network Adapter | NAT (VMnet8)  |

생성이 완료되면 Ubuntu Server 24.04.4 LTS ISO를 연결한다.

---

# Ubuntu Server 설치

Ubuntu Server ISO를 이용하여 운영체제를 설치한다.

## 설치 옵션

| 항목               | 설정값              |
| ------------------ | ------------------- |
| Language           | English             |
| Keyboard Layout    | Korean 또는 English |
| Ubuntu Type        | Ubuntu Server       |
| Installation Type  | Default             |
| OpenSSH Server     | 설치                |
| Additional Package | 선택 안 함          |

설치 완료 후 서버에 로그인한다.

---

# 서버명 설정

현재 서버명을 확인한다.

```bash
hostnamectl
```

서버명을 변경한다.

```bash
sudo hostnamectl set-hostname legacy-ops-01
```

변경 결과를 확인한다.

```bash
hostnamectl
```

정상 적용 시 hostname 항목에 legacy-ops-01이 표시되어야 한다.

---

# 네트워크 인터페이스 확인

고정 IP 설정 전 네트워크 인터페이스명을 확인한다.

```bash
ip addr
```

인터페이스명은 환경에 따라 다를 수 있다.

예시

```text
ens33
ens160
ens192
```

실제 확인된 인터페이스명을 사용하여 설정을 진행한다.

---

# Netplan 설정 파일 확인

Netplan 설정 파일을 확인한다.

```bash
ls /etc/netplan
```

예시

```text
00-installer-config.yaml
```

또는

```text
50-cloud-init.yaml
```

실제 확인된 파일을 수정한다.

---

# 고정 IP 설정

Netplan 설정 파일을 수정한다.

```bash
sudo vi /etc/netplan/<확인된 설정파일명>
```

예시 설정

```yaml
network:
  version: 2
  ethernets:
    <확인된인터페이스명>:
      dhcp4: no
      addresses:
        - 192.168.100.5/24
      routes:
        - to: default
          via: 192.168.100.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

예시

```text
인터페이스명 : ens33
설정파일명 : 00-installer-config.yaml
```

설정을 적용한다.

```bash
sudo netplan apply
```

설정 오류 여부를 확인한다.

```bash
sudo netplan try
```

---

# 네트워크 확인

IP 주소를 확인한다.

```bash
ip addr
```

다음 주소가 확인되어야 한다.

```text
192.168.100.5/24
```

라우팅 정보를 확인한다.

```bash
ip route
```

다음 Gateway가 확인되어야 한다.

```text
default via 192.168.100.1
```

---

# 외부 네트워크 통신 확인

인터넷 연결 상태를 확인한다.

```bash
ping -c 4 8.8.8.8
```

정상 응답이 확인되어야 한다.

---

# DNS 이름 해석 확인

외부 DNS 서버를 이용한 이름 해석을 확인한다.

```bash
ping -c 4 google.com
```

정상 응답이 확인되어야 한다.

---

# OpenSSH 서비스 확인

OpenSSH 서비스 상태를 확인한다.

```bash
sudo systemctl status ssh
```

서비스가 active (running) 상태여야 한다.

부팅 시 자동 시작 여부를 확인한다.

```bash
sudo systemctl is-enabled ssh
```

정상 설정 시 아래 결과가 표시된다.

```text
enabled
```

---

# 구축 완료 기준

다음 항목을 모두 만족해야 한다.

- Ubuntu Server 24.04.4 LTS 설치 완료
- VMware 가상머신 생성 완료
- 서버명 변경 완료
- 고정 IP 설정 완료
- Gateway 설정 완료
- 외부 네트워크 통신 성공
- DNS 이름 해석 성공
- OpenSSH 서비스 정상 동작
- 운영 서버 재부팅 후 정상 로그인 가능

---

# 다음 단계

운영 서버 기본 구축이 완료되면 아래 문서를 진행한다.

- 04-web-server-build.md
