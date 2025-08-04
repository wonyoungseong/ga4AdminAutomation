# GA4 사용자 권한 관리 자동화 시스템

> Google Analytics Admin API를 활용한 현대적인 웹 기반 권한 관리 시스템

## 🎯 프로젝트 개요

GA4를 여러 고객사에 제공/관리하는 서비스 파트너사를 위한 자동화 시스템입니다.
권한 신청부터 만료까지 전 과정을 자동화하여 운영 효율성과 보안을 극대화합니다.

### 주요 기능

- **권한 신청/연장/만료/삭제 자동화**
- **역할 기반 접근 제어 (RBAC)**
  - Super Admin: 시스템 전체 관리
  - Admin: 자신의 고객사 관리
  - Requester: 권한 신청
  - GA User: 권한 연장
- **실시간 알림 시스템**
- **완전한 감사 로그**
- **이메일 기반 권한 연장**

### 기술 스택

#### Frontend
- **Next.js 14+** (App Router)
- **shadcn/ui** 컴포넌트
- **TailwindCSS** 스타일링
- **TypeScript** 타입 안전성
- **Lucide React** 아이콘

#### Backend
- **FastAPI** (Python 3.11+)
- **SQLAlchemy** ORM
- **PostgreSQL** 데이터베이스
- **JWT** 인증
- **Google Analytics Admin API**

#### DevOps
- **Docker** 컨테이너화
- **GitHub Actions** CI/CD
- **AWS/GCP** 클라우드 배포

## 🏗️ 프로젝트 구조

```
.
├── frontend/          # Next.js 프론트엔드
├── backend/           # FastAPI 백엔드
├── shared/           # 공통 타입 정의
├── docs/             # 프로젝트 문서
├── scripts/          # 개발/배포 스크립트
└── legacy-project/   # 이전 버전 참조용
```

## 🚀 빠른 시작

### 사전 요구사항

- Node.js 18+
- Python 3.11+
- PostgreSQL 14+ (또는 다른 호환 데이터베이스)

### 환경 설정

1. **백엔드 환경 설정**
```bash
cd backend
cp .env.example .env
# .env 파일을 수정하여 데이터베이스 및 기타 설정 구성
```

2. **데이터베이스 설정**
```bash
# PostgreSQL 데이터베이스 생성
createdb ga4_admin_dev
```

### 설치 및 실행

1. **백엔드 서버 실행**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **프론트엔드 개발 서버 실행 (새 터미널)**
```bash
cd frontend
npm install
npm run dev
```

3. **접속**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs

### 기본 계정 정보

시스템 테스트를 위한 기본 관리자 계정:
- **이메일**: admin@example.com
- **비밀번호**: admin123

## 🏗️ 개발 현황

### ✅ 완료된 기능
- **백엔드 API 구조**: FastAPI 기반 REST API 서버
- **인증 시스템**: JWT 토큰 기반 인증/인가
- **데이터베이스 모델**: PostgreSQL + SQLAlchemy 2.0
- **프론트엔드 대시보드**: Next.js 14 + shadcn/ui
- **사용자 관리**: CRUD 및 역할 관리
- **반응형 UI**: 데스크톱 중심 반응형 디자인
- **GA4 API 연동**: Google Analytics Admin API 완전 통합
- **권한 관리 로직**: 실제 GA4 권한 부여/해제/연장
- **이메일 알림 시스템**: SMTP 기반 자동 알림 완료
- **감사 로그 시스템**: 모든 활동 추적 및 로깅 완료

### 🎯 API 엔드포인트

**인증 (`/api/auth`)**:
- `POST /register` - 사용자 등록
- `POST /login` - 로그인
- `POST /refresh` - 토큰 갱신
- `GET /me` - 현재 사용자 정보

**사용자 관리 (`/api/users`)**:
- `GET /` - 사용자 목록
- `GET /{user_id}` - 사용자 조회
- `PUT /{user_id}` - 사용자 수정
- `DELETE /{user_id}` - 사용자 삭제

**권한 관리 (`/api/permissions`)**:
- `POST /` - 권한 요청 생성
- `GET /` - 권한 요청 목록
- `GET /{grant_id}` - 권한 요청 조회
- `POST /{grant_id}/approve` - 권한 승인
- `POST /{grant_id}/reject` - 권한 거절
- `POST /{grant_id}/revoke` - 권한 해제
- `POST /{grant_id}/extend` - 권한 연장

**GA4 연동 (`/api/ga4`)**:
- `GET /accounts` - GA4 계정 목록
- `GET /accounts/{account_name}/properties` - 속성 목록
- `GET /properties/{property_name}/users` - 속성 사용자 목록
- `POST /properties/{property_name}/validate` - 속성 접근 검증

**알림 (`/api/notifications`)**:
- `POST /test` - 테스트 알림 발송
- `POST /daily-summary` - 일일 요약 발송
- `GET /settings` - 알림 설정 조회

**감사 로그 (`/api/audit`)**:
- `GET /` - 감사 로그 목록
- `GET /recent` - 최근 활동
- `GET /summary` - 활동 요약 통계
- `GET /count` - 로그 수 조회

### 📋 향후 계획
- **실시간 알림**: WebSocket 기반 실시간 업데이트
- **대시보드 차트**: 시각화 및 통계 차트
- **성능 모니터링**: 시스템 메트릭 수집
- **보안 강화**: 2FA, IP 제한 등
- **자동 만료 관리**: 스케줄러 기반 권한 만료 처리
- **비밀번호 재설정**: 이메일 기반 비밀번호 재설정 UI

## 📖 문서

- [사용자 가이드](./docs/user-guide.md)
- [개발자 가이드](./docs/developer-guide.md)
- [API 문서](./docs/api-reference.md)
- [배포 가이드](./docs/deployment.md)

## 🤝 기여

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원

문제가 있거나 질문이 있으시면 [Issues](../../issues)를 통해 연락주세요.