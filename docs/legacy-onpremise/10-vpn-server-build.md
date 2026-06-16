# VPN 서버 구축 (WireGuard)

## 개요

본 문서는 레거시 온프레미스 환경의 VPN 서버 구축 절차를 정의한다.

VPN 서비스는 재택근무자 또는 외부 관리자가 내부 서버에 안전하게 접속하기 위해 사용한다.

본 환경에서는 별도의 VPN 전용 서버를 추가하지 않고, 운영 서버인 `legacy-ops-01`에 WireGuard를 설치하여 VPN 서비스를 구성한다.

WireGuard를 구성하면 외부 네트워크에 있는 사용자가 VPN 연결 후 내부 서버 관리망에 접근할 수 있다.

---

# 서버 정보

| 항목          | 설정값        |
| ------------- | ------------- |
| 서버명        | legacy-ops-01 |
| 역할          | VPN Server    |
| 서비스        | WireGuard     |
| 내부망 IP     | 192.168.100.5 |
| VPN Server IP | 10.10.10.1    |
| 서비스 포트   | UDP 51820     |

---

# 관리자 계정

| 항목     | 값        |
| -------- | --------- |
| Username | admin     |
| Password | admin1234 |

---

# VPN 네트워크 정보

| 항목                | 설정값        |
| ------------------- | ------------- |
| VPN Network         | 10.10.10.0/24 |
| WireGuard Server IP | 10.10.10.1    |
| VPN User 1 IP       | 10.10.10.10   |
| VPN Interface       | wg0           |
| WireGuard Port      | 51820/UDP     |

`10.10.10.1`은 새로운 서버가 아니라 `legacy-ops-01`의 WireGuard 인터페이스(`wg0`)에 할당되는 VPN 주소이다.

---

# VPN 접근 대상

VPN 연결 후 접근 대상은 다음과 같다.

| 서버명        | 역할                        | IP 주소        |
| ------------- | --------------------------- | -------------- |
| legacy-ops-01 | 운영 서버 / VPN / DNS / NTP | 192.168.100.5  |
| legacy-web-01 | Web Server                  | 192.168.100.10 |
| legacy-app-01 | Application Server          | 192.168.100.20 |
| legacy-db-01  | Database Server             | 192.168.100.30 |

---

# 사전 조건

다음 문서가 완료되어 있어야 한다.

```text
03 OPS Server Build
07 DNS Server Build
08 NTP Server Build
09 Database Backup
```

---

# 운영 서버 접속

운영 서버에 접속한다.

```bash
ssh admin@192.168.100.5
```

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
Static hostname: legacy-ops-01
```

IP 주소를 확인한다.

```bash
ip addr
```

예상 결과

```text
192.168.100.5/24
```

---

# 패키지 업데이트

패키지 정보를 갱신한다.

```bash
sudo apt update
```

설치된 패키지를 업데이트한다.

```bash
sudo apt upgrade -y
```

---

# WireGuard 설치

WireGuard를 설치한다.

```bash
sudo apt install wireguard -y
```

설치 여부를 확인한다.

```bash
dpkg -l | grep wireguard
```

---

# WireGuard 설정 디렉터리 이동

WireGuard 설정 디렉터리로 이동한다.

```bash
cd /etc/wireguard
```

현재 위치를 확인한다.

```bash
pwd
```

예상 결과

```text
/etc/wireguard
```

---

# 서버 키 생성

WireGuard 서버 개인키와 공개키를 생성한다.

```bash
sudo wg genkey | sudo tee server-private.key | sudo wg pubkey | sudo tee server-public.key
```

생성된 파일을 확인한다.

```bash
ls -l
```

예상 결과

```text
server-private.key
server-public.key
```

서버 개인키 권한을 제한한다.

```bash
sudo chmod 600 server-private.key
```

권한을 확인한다.

```bash
ls -l server-private.key
```

---

# 서버 개인키 확인

서버 설정에 사용할 개인키를 확인한다.

```bash
sudo cat /etc/wireguard/server-private.key
```

출력된 값을 `wg0.conf`의 `PrivateKey` 항목에 사용한다.

---

# VPN 사용자 키 생성

VPN User 1의 개인키와 공개키를 생성한다.

```bash
sudo wg genkey | sudo tee user1-private.key | sudo wg pubkey | sudo tee user1-public.key
```

생성된 파일을 확인한다.

```bash
ls -l user1-private.key user1-public.key
```

사용자 개인키 권한을 제한한다.

```bash
sudo chmod 600 user1-private.key
```

---

# VPN 사용자 공개키 확인

서버 설정에 등록할 사용자 공개키를 확인한다.

```bash
sudo cat /etc/wireguard/user1-public.key
```

출력된 값을 `wg0.conf`의 `[Peer] PublicKey` 항목에 사용한다.

---

# IP Forwarding 설정

VPN 사용자가 내부 서버망으로 접근할 수 있도록 IP Forwarding을 활성화한다.

설정 파일을 수정한다.

```bash
sudo vi /etc/sysctl.conf
```

아래 설정을 추가하거나 주석을 해제한다.

```conf
net.ipv4.ip_forward=1
```

설정을 적용한다.

```bash
sudo sysctl -p
```

설정 여부를 확인한다.

```bash
sysctl net.ipv4.ip_forward
```

예상 결과

```text
net.ipv4.ip_forward = 1
```

---

# 내부망 인터페이스 확인

운영 서버의 내부망 인터페이스명을 확인한다.

```bash
ip addr
```

예시

```text
ens33
```

확인된 내부망 인터페이스명을 기록한다.

```text
내부망 인터페이스명: ens33
```

아래 설정에서는 내부망 인터페이스명이 `ens33`인 경우를 기준으로 작성한다.

실제 인터페이스명이 다르면 `ens33` 부분을 실제 인터페이스명으로 변경한다.

---

# WireGuard 서버 설정 파일 생성

설정 파일을 생성한다.

```bash
sudo vi /etc/wireguard/wg0.conf
```

아래 내용을 입력한다.

`<SERVER_PRIVATE_KEY>`에는 `server-private.key` 값을 입력한다.

`<USER1_PUBLIC_KEY>`에는 `user1-public.key` 값을 입력한다.

```ini
[Interface]
Address = 10.10.10.1/24
ListenPort = 51820
PrivateKey = <SERVER_PRIVATE_KEY>

PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o ens33 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o ens33 -j MASQUERADE

[Peer]
PublicKey = <USER1_PUBLIC_KEY>
AllowedIPs = 10.10.10.10/32
```

설정 파일 권한을 제한한다.

```bash
sudo chmod 600 /etc/wireguard/wg0.conf
```

---

# WireGuard 설정 문법 확인

WireGuard 설정을 확인한다.

```bash
sudo wg-quick strip wg0
```

설정 내용이 출력되면 문법상 읽을 수 있는 상태이다.

---

# 방화벽 설정

현재 상태를 확인한다.

```bash
sudo ufw status
```

WireGuard 포트를 허용한다.

```bash
sudo ufw allow 51820/udp
```

상태를 확인한다.

```bash
sudo ufw status
```

예상 결과

```text
51820/udp ALLOW Anywhere
```

---

# WireGuard 서비스 시작

WireGuard 서비스를 시작한다.

```bash
sudo systemctl start wg-quick@wg0
```

상태를 확인한다.

```bash
sudo systemctl status wg-quick@wg0
```

정상 상태 예시

```text
active (exited)
```

---

# 자동 시작 설정

서버 부팅 시 WireGuard가 자동 실행되도록 설정한다.

```bash
sudo systemctl enable wg-quick@wg0
```

자동 시작 여부를 확인한다.

```bash
sudo systemctl is-enabled wg-quick@wg0
```

예상 결과

```text
enabled
```

---

# 서비스 포트 확인

UDP 51820 포트를 확인한다.

```bash
sudo ss -ulpn | grep 51820
```

예상 결과

```text
udp UNCONN 0 0 0.0.0.0:51820
```

---

# VPN 인터페이스 확인

WireGuard 인터페이스를 확인한다.

```bash
ip addr show wg0
```

예상 결과

```text
10.10.10.1/24
```

---

# VPN 상태 확인

WireGuard 상태를 확인한다.

```bash
sudo wg
```

서버 인터페이스와 Peer 정보가 표시되어야 한다.

---

# VPN User 1 클라이언트 설정 파일 생성

사용자에게 전달할 클라이언트 설정 파일을 생성한다.

```bash
sudo vi /etc/wireguard/user1.conf
```

아래 내용을 입력한다.

`<USER1_PRIVATE_KEY>`에는 `user1-private.key` 값을 입력한다.

`<SERVER_PUBLIC_KEY>`에는 `server-public.key` 값을 입력한다.

`<SERVER_PUBLIC_ENDPOINT>`는 실제 외부에서 접속 가능한 서버 주소 또는 포트포워딩 주소로 변경한다.

```ini
[Interface]
PrivateKey = <USER1_PRIVATE_KEY>
Address = 10.10.10.10/24
DNS = 192.168.100.5

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
Endpoint = <SERVER_PUBLIC_ENDPOINT>:51820
AllowedIPs = 192.168.100.0/24, 10.10.10.0/24
PersistentKeepalive = 25
```

설정 파일 권한을 제한한다.

```bash
sudo chmod 600 /etc/wireguard/user1.conf
```

---

# VPN 클라이언트 설정값 확인

사용자 개인키를 확인한다.

```bash
sudo cat /etc/wireguard/user1-private.key
```

서버 공개키를 확인한다.

```bash
sudo cat /etc/wireguard/server-public.key
```

클라이언트 설정 파일을 확인한다.

```bash
sudo cat /etc/wireguard/user1.conf
```

---

# VPN 접속 확인

VPN 클라이언트에서 WireGuard 연결을 수행한다.

연결 후 VPN 서버 주소에 통신 가능한지 확인한다.

```bash
ping 10.10.10.1
```

내부 서버 통신을 확인한다.

```bash
ping 192.168.100.5
```

```bash
ping 192.168.100.10
```

```bash
ping 192.168.100.20
```

```bash
ping 192.168.100.30
```

정상적으로 응답이 반환되어야 한다.

---

# 내부 서버 SSH 접속 확인

VPN 연결 후 내부 서버 SSH 접속을 확인한다.

```bash
ssh admin@192.168.100.5
```

```bash
ssh admin@192.168.100.10
```

```bash
ssh admin@192.168.100.20
```

```bash
ssh admin@192.168.100.30
```

정상적으로 접속되어야 한다.

---

# VPN 상태 재확인

운영 서버에서 VPN 상태를 확인한다.

```bash
sudo wg
```

VPN 클라이언트가 연결된 경우 handshake 정보가 표시된다.

---

# 운영 구조 확인

```text
재택근무자 / 외부 관리자
          │
          ▼
      Internet
          │
          ▼
WireGuard VPN
legacy-ops-01
10.10.10.1
          │
          ▼
내부 서버망
192.168.100.0/24
          │
 ┌────────┼────────┐
 ▼        ▼        ▼
WEB      APP       DB
```

---

# 재부팅 검증

운영 서버를 재부팅한다.

```bash
sudo reboot
```

재접속한다.

```bash
ssh admin@192.168.100.5
```

WireGuard 서비스 상태를 확인한다.

```bash
sudo systemctl status wg-quick@wg0
```

VPN 인터페이스를 확인한다.

```bash
ip addr show wg0
```

포트를 확인한다.

```bash
sudo ss -ulpn | grep 51820
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
10-VPN-Complete
```

---

# 구축 완료 기준

- admin 계정 로그인 가능
- WireGuard 설치 완료
- 서버 키 생성 완료
- 사용자 키 생성 완료
- IP Forwarding 설정 완료
- wg0 설정 파일 생성 완료
- UDP 51820 포트 허용 완료
- WireGuard 서비스 정상 실행
- 자동 시작 설정 완료
- wg0 인터페이스 확인 완료
- VPN 클라이언트 설정 파일 생성 완료
- VPN 서버 IP 통신 확인
- 내부 서버망 통신 확인
- 내부 서버 SSH 접속 확인
- 재부팅 후 정상 동작
- Snapshot 생성 완료

---

# 다음 단계

```text
11 System Validation
```
