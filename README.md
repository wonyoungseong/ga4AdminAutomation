# GA4 Admin Automation

**Google Analytics 4 권한 관리 자동화 시스템**

사용자의 GA4 권한 신청부터 승인, 만료 관리까지 전체 워크플로우를 자동화하는 웹 기반 솔루션입니다.

## 🎯 주요 기능

### ⚡ 자동 승인 시스템
- **Viewer/Analyst 권한**: 신청 즉시 자동 승인 (60일)
- **Editor/Administrator 권한**: 관리자 수동 승인 필요 (7일/90일)

### 📊 관리자 대시보드
- 권한 통계 및 현황 모니터링
- 승인 대기 목록 관리
- 만료 예정 권한 추적
- 권한 철회 및 연장 관리

### 🔐 보안 및 감사
- JWT 기반 인증 시스템
- 역할 기반 접근 제어 (Admin/Requester)
- 모든 작업에 대한 감사 로그
- 중복 신청 방지

### 🔗 GA4 연동
- Google Analytics Admin API 완전 연동
- Service Account 기반 안전한 인증
- 실시간 권한 부여/제거
- 다중 고객사 지원

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd ga4AdminAutomation

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 설정

`.env` 파일을 생성하고 다음 환경 변수를 설정하세요:

```env
# Supabase 설정
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# JWT 설정
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google Analytics 설정
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
GA4_TEST_MODE=true  # 개발 시에는 true로 설정
```

### 3. 데이터베이스 설정

1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. `src/database/migration_001_initial_schema.sql` 실행
3. `src/database/migration_002_permission_system.sql` 실행

### 4. 서버 실행

```bash
# 개발 서버 시작
python -m src.backend.main

# 또는 uvicorn 직접 사용
uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. API 문서 확인

서버가 시작되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📋 API 엔드포인트

### 🔐 인증 (Authentication)
```
POST   /api/v1/auth/login          # 로그인
GET    /api/v1/auth/profile        # 사용자 프로필
GET    /api/v1/auth/verify-token   # 토큰 검증
GET    /api/v1/auth/permissions    # 사용자 권한 확인
```

### 🎫 권한 관리 (Permissions)
```
POST   /api/v1/permissions/request     # 권한 신청
GET    /api/v1/permissions/pending     # 승인 대기 목록 (관리자)
POST   /api/v1/permissions/approve     # 승인/거부 처리 (관리자)
GET    /api/v1/permissions/expiring    # 만료 예정 권한 (관리자)
GET    /api/v1/permissions/stats       # 권한 통계 (관리자)
GET    /api/v1/permissions/active      # 활성 권한 목록 (관리자)
POST   /api/v1/permissions/extend      # 권한 연장 요청
DELETE /api/v1/permissions/{id}/revoke # 권한 철회 (관리자)
```

### 👤 사용자 관리 (Users)
```
GET    /api/v1/users                # 사용자 목록
POST   /api/v1/users                # 사용자 생성
GET    /api/v1/users/{id}           # 특정 사용자 조회
```

### 📊 관리자 (Admin)
```
GET    /api/v1/admin/dashboard      # 대시보드 통계
GET    /api/v1/admin/users          # 사용자 관리
POST   /api/v1/admin/users          # 사용자 생성
GET    /api/v1/admin/stats          # 시스템 통계
```

### 🔗 GA4 연동 (GA4 Integration)
```
GET    /api/v1/ga4/test-connection  # 연결 테스트
POST   /api/v1/ga4/register-user    # 사용자 등록
DELETE /api/v1/ga4/remove-user      # 사용자 제거
GET    /api/v1/ga4/list-users       # 사용자 목록
```

## 🗃️ 데이터베이스 스키마

### 핵심 테이블

- **`website_users`**: 사용자 정보 및 역할 관리
- **`clients`**: 고객사 정보
- **`service_accounts`**: Google Service Account 정보
- **`permission_grants`**: 권한 부여 현황 (핵심 테이블)
- **`audit_logs`**: 모든 작업에 대한 감사 로그

### 주요 관계

```
website_users (1) ←→ (N) permission_grants ←→ (1) clients
                              ↓
                         audit_logs
```

## 🔄 권한 워크플로우

### 자동 승인 (Viewer/Analyst)
1. 사용자가 권한 신청
2. 시스템이 자동으로 승인 여부 판단
3. GA4 API를 통해 즉시 권한 부여
4. 60일 후 자동 만료 설정

### 수동 승인 (Editor/Administrator)
1. 사용자가 권한 신청
2. 관리자에게 승인 요청 알림
3. 관리자가 승인/거부 결정
4. 승인 시 GA4 API를 통해 권한 부여
5. 설정된 기간 후 만료

## 🛠️ 개발 가이드

### 프로젝트 구조

```
src/
├── backend/
│   ├── api/routers/         # API 라우터
│   ├── core/               # 핵심 설정 및 미들웨어
│   ├── models/             # Pydantic 모델
│   └── services/           # 비즈니스 로직
├── database/               # 데이터베이스 마이그레이션
└── tests/                  # 테스트 파일
```

### 개발 원칙

- **SOLID 원칙** 준수
- **Clean Architecture** 적용
- **TDD(Test-Driven Development)** 권장
- 코드 500줄 초과 시 리팩토링

### 코드 품질

```bash
# 포맷팅
black src/
isort src/

# 테스트 실행
pytest src/tests/

# 타입 체크
mypy src/
```

## 📊 시스템 요구사항

### 최소 요구사항
- Python 3.11+
- 메모리: 512MB 이상
- 디스크: 1GB 이상

### 권장 요구사항
- Python 3.11+
- 메모리: 2GB 이상
- 디스크: 5GB 이상

## 🔧 환경별 설정

### 개발 환경
```env
DEBUG=true
GA4_TEST_MODE=true
LOG_LEVEL=DEBUG
```

### 프로덕션 환경
```env
DEBUG=false
GA4_TEST_MODE=false
LOG_LEVEL=INFO
```

## 🤝 기여하기

1. Fork 저장소
2. 새 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 Push (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 📜 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🆘 지원

문제가 발생하거나 질문이 있으면 [Issues](../../issues)에 등록해 주세요.

---

**개발팀**: GA4 Admin Automation Team  
**마지막 업데이트**: 2025년 7월 1일 