# TripKey Admin Web

Vite, React, TypeScript, pnpm 기반 관리자 웹입니다. `integrated-was`의
`/api/admin` API를 사용해 사용자 웹과 동일한 코스 및 예약 데이터를 관리합니다.

## 실행

```bash
pnpm install
pnpm dev
```

기본 개발 주소는 `http://localhost:5174`이며, API 주소를 지정하지 않으면 현재
호스트의 `8000` 포트를 사용합니다.

```bash
cp .env.example .env
```

Mock 모드의 초기 관리자 계정은 `admin` / `password123`입니다.

## 제공 화면

- 관리자 로그인
- 운영 대시보드
- 전체 예약 조회, 일정 변경, 취소
- 코스, 날씨, 활성 예약 현황

## 검증

```bash
pnpm lint
pnpm build
```
