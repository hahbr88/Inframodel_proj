# DNS 서버 구축 (BIND9)

## 개요

본 문서는 레거시 온프레미스 환경의 DNS 서버 구축 절차를 정의한다.

DNS 서버는 사용자가 IP 주소 대신 도메인 이름으로 웹 서비스에 접속할 수 있도록 이름 해석 서비스를 제공한다.

본 환경에서는 운영 서버(`legacy-ops-01`)에 BIND9를 설치하여 내부 DNS 서버를 구축한다.

DNS는 웹 서비스 도메인(`tripkey.shop`)에 대해서만 사용한다.

애플리케이션 서버 및 데이터베이스 서버는 고정 IP 기반으로 운영한다.

---

# 서버 정보

| 항목    | 설정값        |
| ------- | ------------- |
| 서버명  | legacy-ops-01 |
| 역할    | DNS Server    |
| 서비스  | BIND9         |
| IP 주소 | 192.168.100.5 |
| 도메인  | tripkey.shop  |

---

# DNS 적용 대상

| DNS 이름                                    | IP 주소        |
| ------------------------------------------- | -------------- |
| tripkey.shop                                | 192.168.100.10 |
| [www.tripkey.shop](http://www.tripkey.shop) | 192.168.100.10 |

---

# 사전 조건

다음 문서가 완료되어 있어야 한다.

```text
03 OPS Server Build
```

---

# 서버 상태 확인

현재 서버 정보를 확인한다.

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

```bash
sudo apt update
```

```bash
sudo apt upgrade -y
```

---

# BIND9 설치

```bash
sudo apt install -y bind9 bind9-utils dnsutils
```

설치 상태를 확인한다.

```bash
sudo systemctl status bind9
```

정상 상태

```text
active (running)
```

---

# 자동 시작 확인

```bash
sudo systemctl is-enabled bind9
```

정상 결과

```text
enabled
```

---

# DNS 포트 확인

```bash
sudo ss -tulnp | grep ':53'
```

예상 결과

```text
udp 0.0.0.0:53
tcp 0.0.0.0:53
```

---

# Zone 파일 생성

기본 Zone 파일을 복사한다.

```bash
sudo cp /etc/bind/db.local /etc/bind/db.tripkey.shop
```

파일을 확인한다.

```bash
ls -al /etc/bind/db.tripkey.shop
```

---

# Forward Zone 등록

설정 파일을 수정한다.

```bash
sudo vi /etc/bind/named.conf.local
```

아래 내용을 추가한다.

```text
zone "tripkey.shop" {
    type master;
    file "/etc/bind/db.tripkey.shop";
};
```

---

# DNS 레코드 등록

Zone 파일을 수정한다.

```bash
sudo vi /etc/bind/db.tripkey.shop
```

기존 내용을 수정하여 아래와 같이 작성한다.

```text
$TTL 604800

@ IN SOA tripkey.shop. admin.tripkey.shop. (
        1
        604800
        86400
        2419200
        604800
)

@       IN NS   tripkey.shop.

@       IN A    192.168.100.10

www     IN A    192.168.100.10
```

---

# 설정 검증

설정 문법을 확인한다.

```bash
sudo named-checkconf
```

출력이 없으면 정상이다.

Zone 파일을 검증한다.

```bash
sudo named-checkzone tripkey.shop /etc/bind/db.tripkey.shop
```

정상 결과

```text
zone tripkey.shop/IN: loaded serial 1
OK
```

---

# DNS 서비스 재시작

```bash
sudo systemctl restart bind9
```

```bash
sudo systemctl status bind9
```

---

# DNS 조회 테스트

```bash
dig @192.168.100.5 tripkey.shop
```

예상 결과

```text
tripkey.shop. IN A 192.168.100.10
```

---

```bash
dig @192.168.100.5 www.tripkey.shop
```

예상 결과

```text
www.tripkey.shop. IN A 192.168.100.10
```

---

# nslookup 테스트

```bash
nslookup tripkey.shop 192.168.100.5
```

---

```bash
nslookup www.tripkey.shop 192.168.100.5
```

---

# 클라이언트 DNS 설정

모든 서버는 DNS 서버로 `192.168.100.5`를 사용한다.

설정 후 확인한다.

```bash
dig tripkey.shop
```

```bash
dig www.tripkey.shop
```

---

# 서비스 구조

```text
사용자
↓
tripkey.shop
↓
192.168.100.10
↓
legacy-web-01
↓
legacy-app-01
↓
legacy-db-01
```

---

# 재부팅 검증

```bash
sudo reboot
```

재접속 후 확인한다.

```bash
sudo systemctl status bind9
```

```bash
sudo ss -tulnp | grep ':53'
```

```bash
dig @192.168.100.5 tripkey.shop
```

---

# 구축 완료 기준

- BIND9 설치 완료
- Zone 파일 생성 완료
- tripkey.shop 등록 완료
- [www.tripkey.shop](http://www.tripkey.shop) 등록 완료
- DNS 조회 성공
- BIND9 정상 동작
- 재부팅 후 정상 동작

---

# 다음 단계

```text
08 NTP Server Build
```
