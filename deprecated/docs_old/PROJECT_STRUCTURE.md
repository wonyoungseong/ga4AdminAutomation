# GA4 권한 관리 시스템 - 프로젝트 구조

## 📁 폴더 구조

```
ga4AdminAutomation/
├── 📂 src/                          # 소스 코드
│   ├── 📂 api/                      # API 관련 모듈
│   ├── 📂 core/                     # 핵심 기능 모듈
│   ├── 📂 domain/                   # 도메인 엔티티
│   ├── 📂 infrastructure/           # 인프라 관련 코드
│   ├── 📂 services/                 # 비즈니스 로직 서비스
│   └── 📂 web/                      # 웹 애플리케이션
│
├── 📂 tests/                        # 테스트 코드
│   ├── 📂 integration/              # 통합 테스트
│   ├── 📂 unit/                     # 단위 테스트
│   ├── 📂 e2e/                      # E2E 테스트
│   └── 📂 performance/              # 성능 테스트
│
├── 📂 docs/                         # 문서
│   ├── 📂 api/                      # API 문서
│   ├── 📂 guides/                   # 가이드 문서
│   ├── 📂 reports/                  # 프로젝트 보고서
│   └── 📂 architecture/             # 아키텍처 문서
│
├── 📂 tools/                        # 유틸리티 도구
├── 📂 scripts/                      # 실행 스크립트
├── 📂 config/                       # 설정 파일
├── 📂 data/                         # 데이터베이스 파일
├── 📂 logs/                         # 로그 파일
├── 📂 backups/                      # 백업 파일
├── 📂 temp/                         # 임시 파일
├── 📂 legacy/                       # 레거시 코드
└── 📂 archive/                      # 아카이브된 코드

## 주요 파일

- `start_web_server.py`             # 웹 서버 시작 스크립트
- `main.py`                         # 메인 애플리케이션
- `requirements.txt`                # Python 의존성
- `config.json`                     # 설정 파일
- `README.md`                       # 프로젝트 소개

## 📂 src/ 상세 구조

### api/
- `scheduler.py`                    # 스케줄러 서비스
- `invitation_api.py`               # 초대 API

### core/
- `ga4_automation.py`               # GA4 자동화 핵심 로직
- `logger.py`                       # 로깅 시스템
- `email_validator.py`              # 이메일 검증
- `gmail_service.py`                # Gmail 서비스
- `interfaces.py`                   # 인터페이스 정의

### services/
- `ga4_user_manager.py`             # GA4 사용자 관리
- `notification_service.py`         # 알림 서비스
- `property_scanner_service.py`     # 프로퍼티 스캔 서비스

### web/
- `main.py`                         # FastAPI 웹 애플리케이션
- `templates/`                      # HTML 템플릿
- `static/`                         # 정적 파일

### infrastructure/
- `database.py`                     # 데이터베이스 관리
- `test_helpers.py`                 # 테스트 헬퍼

## 🧪 tests/ 구조

### integration/
통합 테스트 파일들 - 여러 컴포넌트 간의 상호작용 테스트

### unit/
단위 테스트 파일들 - 개별 함수/클래스 테스트

### e2e/
End-to-End 테스트 - 전체 시스템 플로우 테스트

### performance/
성능 테스트 - 시스템 성능 및 부하 테스트

## 📚 docs/ 구조

### api/
API 문서 및 스펙

### guides/
- 사용자 가이드
- 개발자 가이드
- 설치 가이드

### reports/
- 프로젝트 진행 보고서
- 테스트 결과 보고서
- 시스템 상태 보고서

### architecture/
- 시스템 아키텍처 문서
- 데이터베이스 설계 문서 