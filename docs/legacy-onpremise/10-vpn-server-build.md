# VPN 서버 구축 (WireGuard)

## 개요

본 문서는 레거시 온프레미스 환경의 VPN 서버 구축 절차를 정의한다.

VPN 서비스는 재택근무자 또는 외부 관리자가 내부 서버에 안전하게 접속하기 위해 사용한다.

본 환경에서는 별도의 VPN 전용 서버를 추가하지 않고, 운영 서버인 `legacy-ops-01`에 WireGuard를 설치하여 VPN 서비스를 구성한다.

WireGuard를 구성하면 외부 네트워크에 있는 사용자가 VPN 연결 후 내부 서버 관리망에 접근할 수 있다.

---

# 서버 정보

| 항목        | 설정값        |
| ----------- | ------------- |
| 서버명      | legacy-ops-01 |
| 역할        | VPN Server    |
| 서비스      | WireGuard     |
| 내부망 IP   | 192.168.100.5 |
| 서비스 포트 | UDP 51820     |

`legacy-ops-01`은 기존 운영 서버이며, WireGuard 설치 후 VPN 서버 역할을 함께 수행한다.

즉, VPN 서버를 별도로 추가하는 것이 아니라 운영 서버에 VPN 기능을 구성하는 방식이다.

---

# VPN 네트워크 정보

| 항목                | 설정값                    |
| ------------------- | ------------------------- |
| VPN Network         | 10.10.10.0/24             |
| WireGuard Server IP | 10.10.10.1                |
| VPN User IP Range   | 10.10.10.10 ~ 10.10.10.99 |

WireGuard VPN 인터페이스인 `wg0`에 VPN 네트워크 주소를 할당한다.

본 환경에서 `legacy-ops-01`은 다음과 같이 두 개의 네트워크 주소를 가진다.

| 인터페이스 | IP 주소       | 설명             |
| ---------- | ------------- | ---------------- |
| eth0       | 192.168.100.5 | 내부 서버망 IP   |
| wg0        | 10.10.10.1    | WireGuard VPN IP |

`10.10.10.1`은 새로운 서버가 아니라, `legacy-ops-01`의 WireGuard 인터페이스에 할당되는 VPN 주소이다.

---

# VPN 서비스 목적

VPN은 외부 사용자에게 웹 서비스를 제공하기 위한 용도가 아니다.

본 환경에서 VPN은 재택근무자 또는 외부 관리자가 내부 서버에 안전하게 접속하기 위한 관리용 접속 수단이다.

VPN 연결 후 접근 대상 서버는 다음과 같다.

| 서버명        | 역할                  |
| ------------- | --------------------- |
| legacy-ops-01 | 운영 서버 / VPN / DNS |
| legacy-web-01 | Web Server            |
| legacy-app-01 | Application Server    |
| legacy-db-01  | Database Server       |

VPN 사용자는 WireGuard VPN 연결 후 내부 네트워크에 접속하여 서버에 접근할 수 있다.

---

# VPN IP 할당 기준

VPN 서버는 `10.10.10.1`을 사용한다.

VPN 사용자는 `10.10.10.10`부터 순차적으로 할당한다.

예시

| 구분             | VPN IP      |
| ---------------- | ----------- |
| WireGuard Server | 10.10.10.1  |
| VPN User 1       | 10.10.10.10 |
| VPN User 2       | 10.10.10.11 |
| VPN User 3       | 10.10.10.12 |
| VPN User 4       | 10.10.10.13 |

사용자 IP는 필요에 따라 추가할 수 있다.

단, VPN 서버 IP와 사용자 IP는 서로 중복되면 안 된다.

---

# 패키지 업데이트

패키지 정보를 최신 상태로 갱신한다.

```bash
sudo apt update
```

---

# WireGuard 설치

WireGuard를 설치한다.

```bash
sudo apt install wireguard -y
```

설치 완료 후 패키지를 확인한다.

```bash
dpkg -l | grep wireguard
```

---

# WireGuard 설정 디렉터리 이동

WireGuard 설정 디렉터리로 이동한다.

```bash
cd /etc/wireguard
```

---

# 서버 키 생성

WireGuard 서버에서 사용할 개인키와 공개키를 생성한다.

```bash
sudo wg genkey | sudo tee server-private.key | sudo wg pubkey | sudo tee server-public.key
```

생성된 파일을 확인한다.

```bash
ls -l
```

예시

```text
server-private.key
server-public.key
```

개인키는 외부에 노출되면 안 된다.

서버 개인키 파일 권한을 제한한다.

```bash
sudo chmod 600 server-private.key
```

---

# 서버 개인키 확인

서버 설정 파일에 입력할 개인키를 확인한다.

```bash
sudo cat /etc/wireguard/server-private.key
```

출력된 값을 서버 설정 파일의 `PrivateKey` 항목에 사용한다.

---

# IP Forwarding 설정

VPN 사용자가 내부 서버망으로 접근하려면 서버에서 패킷 전달 기능이 활성화되어야 한다.

IP Forwarding 설정 파일을 수정한다.

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

설정 적용 여부를 확인한다.

```bash
sysctl net.ipv4.ip_forward
```

확인 결과

```text
net.ipv4.ip_forward = 1
```

이어야 한다.

---

# 서버 설정 파일 생성

WireGuard 서버 설정 파일을 생성한다.

```bash
sudo vi /etc/wireguard/wg0.conf
```

설정 예시

```ini
[Interface]
Address = 10.10.10.1/24
ListenPort = 51820
PrivateKey = <SERVER_PRIVATE_KEY>

[Peer]
PublicKey = <USER1_PUBLIC_KEY>
AllowedIPs = 10.10.10.10/32
```

설정 항목 설명

| 항목       | 설명                          |
| ---------- | ----------------------------- |
| Address    | WireGuard VPN 인터페이스 주소 |
| ListenPort | WireGuard 서비스 포트         |
| PrivateKey | WireGuard 서버 개인키         |
| PublicKey  | VPN 사용자 공개키             |
| AllowedIPs | 해당 사용자가 사용할 VPN IP   |

`Address = 10.10.10.1/24`는 WireGuard 서버가 VPN 네트워크 `10.10.10.0/24`를 사용한다는 의미이다.

`AllowedIPs = 10.10.10.10/32`는 해당 VPN 사용자에게 `10.10.10.10` 하나의 IP만 할당한다는 의미이다.

---

# 사용자 추가 기준

사용자가 추가될 경우 `[Peer]` 항목을 추가한다.

예시

```ini
[Peer]
PublicKey = <USER1_PUBLIC_KEY>
AllowedIPs = 10.10.10.10/32

[Peer]
PublicKey = <USER2_PUBLIC_KEY>
AllowedIPs = 10.10.10.11/32

[Peer]
PublicKey = <USER3_PUBLIC_KEY>
AllowedIPs = 10.10.10.12/32
```

각 사용자는 서로 다른 VPN IP를 사용해야 한다.

동일한 `AllowedIPs`를 여러 사용자에게 중복 설정하면 안 된다.

---

# WireGuard 서비스 시작

WireGuard 서비스를 시작한다.

```bash
sudo systemctl start wg-quick@wg0
```

서비스 상태를 확인한다.

```bash
sudo systemctl status wg-quick@wg0
```

상태가 `active (exited)` 또는 정상 실행 상태로 표시되어야 한다.

---

# 자동 시작 설정

서버 부팅 시 WireGuard가 자동 실행되도록 설정한다.

```bash
sudo systemctl enable wg-quick@wg0
```

자동 시작 설정 여부를 확인한다.

```bash
sudo systemctl is-enabled wg-quick@wg0
```

확인 결과

```text
enabled
```

이어야 한다.

---

# 서비스 포트 확인

WireGuard 서비스 포트를 확인한다.

```bash
ss -ulpn | grep 51820
```

UDP 51820 포트가 확인되어야 한다.

---

# VPN 인터페이스 확인

WireGuard 인터페이스가 생성되었는지 확인한다.

```bash
ip addr show wg0
```

확인 결과에 `10.10.10.1/24`가 표시되어야 한다.

예시

```text
inet 10.10.10.1/24
```

---

# VPN 상태 확인

WireGuard 상태를 확인한다.

```bash
sudo wg
```

설정된 Peer 정보가 표시되어야 한다.

VPN 사용자가 접속한 경우 handshake 정보가 표시된다.

---

# VPN 접속 확인

VPN 클라이언트에서 WireGuard 연결을 수행한다.

연결 성공 후 VPN 서버 주소에 통신 가능한지 확인한다.

```bash
ping 10.10.10.1
```

내부 서버에도 통신 가능한지 확인한다.

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

# 내부 서버 접근 확인

VPN 연결 후 내부 서버 SSH 접속을 확인한다.

예시

```bash
ssh <USER>@192.168.100.5
```

```bash
ssh <USER>@192.168.100.10
```

```bash
ssh <USER>@192.168.100.20
```

```bash
ssh <USER>@192.168.100.30
```

접속 계정과 권한은 서버별 운영 정책에 따른다.

---

# 운영 구조

```text
재택근무자 / 외부 관리자
          │
          ▼
      Internet
          │
          ▼
WireGuard VPN
(legacy-ops-01)
          │
          ▼
내부 서버망 192.168.100.0/24
          │
 ┌────────┼────────┐
 ▼        ▼        ▼
WEB      APP       DB
```

`legacy-ops-01`은 내부망 IP `192.168.100.5`와 VPN IP `10.10.10.1`을 함께 사용한다.

VPN 사용자는 WireGuard 연결 후 내부 서버망에 접근할 수 있다.

---

# 점검 항목

| 점검 항목                   | 확인 |
| --------------------------- | ---- |
| WireGuard 설치 완료         | □    |
| 서버 키 생성 완료           | □    |
| 서버 개인키 권한 설정 완료  | □    |
| VPN 네트워크 대역 설정 완료 | □    |
| IP Forwarding 설정 완료     | □    |
| wg0 설정 파일 생성 완료     | □    |
| Peer 설정 완료              | □    |
| WireGuard 서비스 시작 완료  | □    |
| 자동 시작 설정 완료         | □    |
| UDP 51820 포트 확인         | □    |
| wg0 인터페이스 확인         | □    |
| VPN 서버 IP 통신 확인       | □    |
| 내부 서버 통신 확인         | □    |
| 내부 서버 SSH 접속 확인     | □    |

---

# 구축 완료 기준

다음 항목을 모두 만족하면 VPN 서버 구축이 완료된 것으로 판단한다.

- WireGuard 설치 완료
- 서버 키 생성 완료
- `wg0.conf` 설정 완료
- IP Forwarding 활성화
- WireGuard 서비스 정상 실행
- UDP 51820 포트 확인
- VPN 클라이언트 접속 성공
- VPN 서버 IP `10.10.10.1` 통신 성공
- 내부 서버망 `192.168.100.0/24` 통신 성공
- 내부 서버 SSH 접속 확인

---

# 다음 단계

VPN 서버 구축이 완료되면 아래 문서를 진행한다.

- 11-system-validation.md
