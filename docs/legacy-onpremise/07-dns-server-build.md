# DNS 서버 구축 (BIND9)

## 개요

본 문서는 레거시 온프레미스 환경의 DNS 서버 구축 절차를 정의한다.

DNS(Domain Name System)는 IP 주소를 사람이 이해하기 쉬운 도메인 이름으로 변환하는 서비스이다.

본 환경에서는 운영 서버(`legacy-ops-01`)에 BIND9를 설치하여 내부 DNS 서버를 구축한다.

DNS를 적용하면 서버 간 통신 및 운영 시 IP 주소 대신 이름을 사용할 수 있으며, 서버 IP 변경 시 DNS 레코드만 수정하면 되므로 운영 효율성을 높일 수 있다.

예시

```text
192.168.100.10
↓
tripkey.shop

192.168.100.30
↓
db.tripkey.shop
```

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

| 서버명        | 역할               | IP 주소        | DNS 이름                       |
| ------------- | ------------------ | -------------- | ------------------------------ |
| legacy-ops-01 | DNS / NTP / Backup | 192.168.100.5  | ops.tripkey.shop               |
| legacy-web-01 | Web Server         | 192.168.100.10 | tripkey.shop, web.tripkey.shop |
| legacy-app-01 | Application Server | 192.168.100.20 | app.tripkey.shop               |
| legacy-db-01  | Database Server    | 192.168.100.30 | db.tripkey.shop                |

---

# DNS 서비스 목적

본 환경의 DNS 서버는 다음 목적으로 운영한다.

- 웹 서비스 도메인 제공
- 서버 간 이름 기반 통신
- 서버 식별 체계 통일
- IP 변경 시 설정 변경 최소화

예시

```text
DB 연결

기존
192.168.100.30

변경
db.tripkey.shop
```

---

# 패키지 업데이트

패키지 정보를 최신 상태로 갱신한다.

```bash
sudo apt update
```

---

# BIND9 설치

DNS 서비스를 위한 BIND9 패키지를 설치한다.

```bash
sudo apt install bind9 bind9-utils -y
```

설치 상태를 확인한다.

```bash
sudo systemctl status bind9
```

---

# 서비스 자동 시작 확인

서버 재부팅 시 자동 실행 여부를 확인한다.

```bash
sudo systemctl is-enabled bind9
```

정상 결과

```text
enabled
```

---

# DNS 서비스 포트 확인

DNS 서비스가 사용하는 53번 포트가 열려 있는지 확인한다.

```bash
ss -tulpen | grep ':53'
```

정상 결과 예시

```text
udp UNCONN 0 0 0.0.0.0:53
tcp LISTEN 0 10 0.0.0.0:53
```

---

# Zone 파일 생성

기본 Zone 파일을 복사하여 프로젝트용 Zone 파일을 생성한다.

```bash
sudo cp /etc/bind/db.local /etc/bind/db.tripkey.shop
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

다음 내용으로 구성한다.

```text
$TTL 604800

@ IN SOA ops.tripkey.shop. admin.tripkey.shop. (
        2
        604800
        86400
        2419200
        604800
)

@       IN NS   ops.tripkey.shop.

@       IN A    192.168.100.10

ops     IN A    192.168.100.5
web     IN A    192.168.100.10
app     IN A    192.168.100.20
db      IN A    192.168.100.30
```

---

# DNS 레코드 설명

| DNS 이름         | IP 주소        | 설명                     |
| ---------------- | -------------- | ------------------------ |
| tripkey.shop     | 192.168.100.10 | 메인 웹 서비스           |
| web.tripkey.shop | 192.168.100.10 | 웹 서버 식별용           |
| app.tripkey.shop | 192.168.100.20 | 애플리케이션 서버 식별용 |
| db.tripkey.shop  | 192.168.100.30 | 데이터베이스 서버 식별용 |
| ops.tripkey.shop | 192.168.100.5  | 운영 서버 식별용         |

---

# 설정 검증

BIND9 설정 문법을 검증한다.

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
zone tripkey.shop/IN: loaded serial 2
OK
```

---

# DNS 서비스 재시작

설정을 적용한다.

```bash
sudo systemctl restart bind9
```

상태를 확인한다.

```bash
sudo systemctl status bind9
```

---

# DNS 조회 테스트

메인 도메인 조회

```bash
dig @192.168.100.5 tripkey.shop
```

정상 결과

```text
tripkey.shop. 604800 IN A 192.168.100.10
```

웹 서버 조회

```bash
dig @192.168.100.5 web.tripkey.shop
```

애플리케이션 서버 조회

```bash
dig @192.168.100.5 app.tripkey.shop
```

DB 서버 조회

```bash
dig @192.168.100.5 db.tripkey.shop
```

운영 서버 조회

```bash
dig @192.168.100.5 ops.tripkey.shop
```

---

# nslookup 테스트

```bash
nslookup tripkey.shop 192.168.100.5
```

정상 결과

```text
Name: tripkey.shop
Address: 192.168.100.10
```

```bash
nslookup app.tripkey.shop 192.168.100.5
```

```bash
nslookup db.tripkey.shop 192.168.100.5
```

```bash
nslookup ops.tripkey.shop 192.168.100.5
```

---

# 클라이언트 DNS 설정

모든 서버는 DNS 서버를 `legacy-ops-01`로 사용하도록 설정한다.

```text
DNS Server
192.168.100.5
```

설정 후 이름 기반 조회를 수행한다.

```bash
dig tripkey.shop
dig web.tripkey.shop
dig app.tripkey.shop
dig db.tripkey.shop
dig ops.tripkey.shop
```

---

# 운영 관점 설명

DNS는 서버를 IP 주소가 아닌 이름으로 관리하기 위해 사용한다.

레거시 환경에서는 서버 간 통신 시 IP 주소를 직접 사용하는 경우가 많지만, 서버 증설 또는 IP 변경 시 관리 부담이 증가한다.

DNS를 적용하면 서비스와 서버를 이름 기반으로 관리할 수 있으며 운영 편의성이 향상된다.

예시

```text
Application Server
↓
db.tripkey.shop
↓
192.168.100.30
```

DB 서버 IP가 변경되더라도 DNS 레코드만 수정하면 되므로 애플리케이션 설정 변경을 최소화할 수 있다.

또한 운영자는 IP 주소 대신 역할 기반 이름으로 서버를 식별할 수 있으므로 유지보수 효율성을 높일 수 있다.

---

# 점검 항목

| 점검 항목                  | 확인 |
| -------------------------- | ---- |
| BIND9 설치 완료            | □    |
| 서비스 실행 확인           | □    |
| 자동 시작 설정 확인        | □    |
| 53번 포트 확인             | □    |
| Zone 생성 완료             | □    |
| Zone 등록 완료             | □    |
| DNS 레코드 등록 완료       | □    |
| named-checkconf 검증 완료  | □    |
| named-checkzone 검증 완료  | □    |
| tripkey.shop 조회 성공     | □    |
| web.tripkey.shop 조회 성공 | □    |
| app.tripkey.shop 조회 성공 | □    |
| db.tripkey.shop 조회 성공  | □    |
| ops.tripkey.shop 조회 성공 | □    |
| DNS 설정 적용 완료         | □    |

---

# 구축 완료 기준

다음 항목을 모두 만족하면 DNS 서버 구축이 완료된 것으로 판단한다.

- BIND9 설치 완료
- Zone 파일 생성 완료
- DNS 레코드 등록 완료
- BIND9 정상 실행
- tripkey.shop 조회 성공
- web.tripkey.shop 조회 성공
- app.tripkey.shop 조회 성공
- db.tripkey.shop 조회 성공
- ops.tripkey.shop 조회 성공
- 모든 서버 DNS 설정 완료

---

# 다음 단계

DNS 서버 구축이 완료되면 다음 문서를 진행한다.

- 08-ntp-chrony.md
