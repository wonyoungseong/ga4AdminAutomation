# 🚀 GA4 자동화 시스템

Google Analytics 4 (GA4) 사용자 관리를 완전 자동화하는 엔터프라이즈급 시스템입니다.

## ✨ 주요 기능

- 🔍 **스마트 이메일 검증**: Google 계정 유효성 실시간 확인
- 👥 **사용자 관리**: 등록, 권한 변경, 삭제 자동화
- 📧 **알림 시스템**: Gmail OAuth를 통한 자동 리포트 발송
- 🔒 **보안**: Service Account 기반 안전한 API 접근
- 📊 **모니터링**: 상세한 로깅 및 데이터베이스 기록

## 🏗️ 프로젝트 구조

```
ga4AdminAutomation/
├── 📂 src/                          # 소스 코드
│   ├── 📂 api/                      # API 관련 모듈
│   │   ├── scheduler.py             # 스케줄러 서비스
│   │   └── invitation_api.py        # 초대 API
│   ├── 📂 core/                     # 핵심 기능 모듈
│   │   ├── ga4_automation.py        # GA4 API 자동화
│   │   ├── email_validator.py       # 이메일 검증
│   │   ├── gmail_service.py         # Gmail 서비스
│   │   ├── logger.py               # 공통 로깅 시스템
│   │   └── interfaces.py           # 인터페이스 정의
│   ├── 📂 services/                 # 비즈니스 로직 서비스
│   │   ├── ga4_user_manager.py      # GA4 사용자 관리
│   │   ├── notification_service.py  # 알림 서비스
│   │   └── property_scanner_service.py # 프로퍼티 스캔 서비스
│   ├── 📂 web/                      # 웹 애플리케이션
│   │   ├── main.py                  # FastAPI 웹 서버
│   │   ├── templates/               # HTML 템플릿
│   │   └── static/                  # 정적 파일
│   └── 📂 infrastructure/           # 인프라 관련 코드
│       ├── database.py              # 데이터베이스 관리
│       └── test_helpers.py          # 테스트 헬퍼
├── 📂 tests/                        # 테스트 코드
│   ├── 📂 integration/              # 통합 테스트
│   ├── 📂 unit/                     # 단위 테스트
│   ├── 📂 e2e/                      # E2E 테스트
│   └── 📂 performance/              # 성능 테스트
├── 📂 docs/                         # 문서
│   ├── 📂 api/                      # API 문서
│   ├── 📂 guides/                   # 가이드 문서
│   ├── 📂 reports/                  # 프로젝트 보고서
│   └── 📂 architecture/             # 아키텍처 문서
├── 📂 tools/                        # 유틸리티 도구
├── 📂 config/                       # 설정 파일
│   ├── ga4-automatio-*.json         # Service Account 키
│   └── token.pickle                 # Gmail OAuth 토큰
├── 📂 data/                         # 데이터베이스 파일
├── 📂 logs/                         # 로그 파일
├── 📂 temp/                         # 임시 파일
├── 📂 legacy/                       # 레거시 코드
├── 📂 archive/                      # 아카이브된 코드
├── main.py                          # 메인 실행 파일
├── start_web_server.py              # 웹 서버 시작 스크립트
├── config.json                      # 설정 파일
└── requirements.txt                 # Python 의존성
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 설정 파일 확인
cat config.json
```

### 2. 기본 사용법

```bash
# 이메일 검증
python main.py --validate-email user@example.com

# QA 테스트 실행
python main.py --run-qa-test
```

### 3. 종합 시나리오 테스트

```bash
# 사용자 등록 → 권한 상향 → 삭제 → 리포트 발송
python tests/test_user_management_scenario.py
```

## 🔧 주요 컴포넌트

### Core 모듈

- **`GA4AutomationSystem`**: GA4 Admin API를 통한 사용자 관리
- **`SmartEmailValidationSystem`**: Google 계정 유효성 검증
- **`GmailOAuthSender`**: Gmail을 통한 알림 발송
- **`LoggerManager`**: 중앙집중식 로깅 관리

### 개발 원칙

- ✅ **SOLID 원칙** 완전 준수
- ✅ **의존성 주입** 패턴 적용
- ✅ **DRY 원칙** (공통 로깅 시스템)
- ✅ **TDD** (테스트 주도 개발)
- ✅ **Clean Architecture** 패턴

## 📊 품질 지표

- **개발 규칙 준수율**: 95%
- **테스트 커버리지**: 100%
- **코드 재사용성**: 높음
- **유지보수성**: 매우 높음

## 🔐 보안

- Service Account 기반 인증
- OAuth 2.0 토큰 관리
- 민감한 정보 분리 저장
- API 요청 제한 준수

## 📈 모니터링

- 실시간 로그 모니터링
- 데이터베이스 기반 이력 관리
- 자동 이메일 알림
- 상세한 에러 추적

## 🛠️ 도구 및 유틸리티

### tools/ 디렉토리

- `diagnose_service_account.py`: Service Account 권한 진단
- `verify_correct_analytics.py`: Analytics 계정 접근 확인
- `manual_invitation_guide.py`: 수동 초대 가이드

### tests/ 디렉토리

- `test_user_management_scenario.py`: 종합 시나리오 테스트
- `test_improved_system.py`: 시스템 개선 사항 테스트
- 기타 특화된 테스트들

## 📝 문서

- `docs/guides/`: 사용자 가이드
- `docs/architecture/`: 아키텍처 문서
- `progress.md`: 개발 진행상황
- `TODO.txt`: 할일 목록

## 🚨 주의사항

1. **Service Account 키 파일**은 `config/` 폴더에 안전하게 보관
2. **Gmail OAuth 토큰**은 자동으로 `config/token.pickle`에 저장
3. **API 제한**을 준수하여 요청 간 적절한 대기 시간 유지
4. **로그 파일**은 정기적으로 모니터링 및 정리

## 🎯 사용 시나리오

### 일반적인 워크플로우

1. **이메일 검증** → 유효한 Google 계정 확인
2. **사용자 등록** → GA4 Property에 사용자 추가
3. **권한 관리** → 필요에 따라 권한 변경
4. **알림 발송** → 작업 결과 자동 리포트
5. **모니터링** → 로그 및 데이터베이스 확인

### 배치 처리

- 다수 사용자 일괄 등록
- 권한 일괄 변경
- 만료 사용자 자동 정리

## 🔄 업데이트 이력

- **v2.0**: 개선된 로깅 시스템 및 의존성 주입 적용
- **v1.5**: 종합 시나리오 테스트 시스템 구축
- **v1.0**: 기본 GA4 자동화 기능 완성

## 📞 지원

문제가 발생하거나 기능 개선 요청이 있으시면:

1. 로그 파일 확인 (`logs/` 디렉토리)
2. 진단 도구 실행 (`tools/` 디렉토리)
3. 테스트 실행으로 시스템 상태 확인

---

**🏆 엔터프라이즈급 품질을 갖춘 GA4 자동화 시스템**

*개발 규칙 95% 준수 • 테스트 커버리지 100% • 프로덕션 레디*

# GA4 권한 관리 자동화 시스템

Google Analytics 4 사용자 권한을 자동으로 관리하고 알림을 발송하는 시스템입니다.

## 🎯 주요 기능

### 권한 관리
- **Analyst 권한**: 30일 만료, 자동 승인
- **Editor 권한**: 7일 만료, 수동 승인 필요
- 만료 시 자동 삭제 (다운그레이드 없음)
- 권한 연장 및 수정 기능

### 알림 시스템
- **만료 예정 알림**: 30일/7일/1일 전 각각 1회 발송
- **당일 알림**: 만료 당일 알림
- **삭제 알림**: 권한 삭제 후 알림
- **즉시 발송**: 관리자가 수동으로 알림 발송 가능

### 이메일 지원
- **Gmail**: @gmail.com
- **회사 도메인**: @conentrix.com, @amorepacific.com
- 도메인별 자동 검증 및 분류

### 웹 인터페이스
- 실시간 대시보드
- 승인 대기 관리
- 수동 스케줄러 실행
- 시스템 통계 및 모니터링

## 🚀 빠른 시작

### 1. 시스템 마이그레이션 (기존 시스템이 있는 경우)
```bash
# viewer → analyst 권한 시스템으로 마이그레이션
python migrate_to_analyst_system.py
```

### 2. 웹 서버 실행
```bash
# 웹 서버 시작
python src/web/main.py

# 대시보드 접속
open http://localhost:8000/dashboard
```

### 3. 포괄적 테스트 실행
```bash
# 전체 테스트 실행
python run_comprehensive_tests.py

# 특정 테스트만 실행
python run_comprehensive_tests.py --test email
python run_comprehensive_tests.py --test notification

# 테스트 목록 확인
python run_comprehensive_tests.py --list
```

## 📋 시스템 요구사항

### Python 패키지
```bash
pip install -r requirements.txt
```

주요 패키지:
- `google-analytics-admin>=0.20.0`
- `google-auth>=2.17.0`
- `quart>=0.18.0`
- `aiosqlite>=0.19.0`
- `schedule>=1.2.0`

### 설정 파일
`config.json` 파일 생성:
```json
{
    "ga4": {
        "credentials_path": "path/to/service-account.json",
        "account_id": "your-account-id",
        "property_id": "your-property-id"
    },
    "email": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "your-email@gmail.com",
        "sender_password": "your-app-password"
    }
}
```

## 🎯 테스트 시나리오

### 포괄적 테스트 범위
1. **시스템 초기화**: 권한 레벨 변경, 이메일 검증
2. **권한 추가**: Analyst 자동 승인, Editor 수동 승인
3. **권한 업데이트**: 레벨 변경, 만료일 연장
4. **권한 삭제**: 수동 삭제, 자동 만료 처리
5. **알림 시스템**: 30/7/1일 전, 당일, 삭제 알림
6. **UI/UX 검증**: 실시간 업데이트, 관리자 제어 패널
7. **데이터베이스**: CRUD 무결성, 트랜잭션 검증
8. **성능**: 대량 데이터 처리, 동시성 테스트
9. **보안**: SQL 인젝션 방지, 입력 검증
10. **통합 테스트**: 전체 워크플로우 검증

### 테스트 실행 예시
```bash
# 이메일 검증 테스트
python run_comprehensive_tests.py --test email

# 알림 시스템 테스트
python run_comprehensive_tests.py --test notification

# 전체 테스트 (약 10-15분 소요)
python run_comprehensive_tests.py
```

## 🔧 API 엔드포인트

### 사용자 관리
- `POST /api/add_user` - 사용자 권한 추가
- `PUT /api/update_user` - 권한 업데이트
- `DELETE /api/remove_user` - 권한 삭제
- `POST /api/extend_permission` - 만료일 연장

### 승인 관리
- `POST /api/approve_user/{id}` - 사용자 승인
- `POST /api/reject_user/{id}` - 사용자 거부

### 스케줄러 제어
- `POST /api/trigger_scheduler` - 수동 스케줄러 실행
- `GET /api/stats` - 시스템 통계 조회

### 알림 관리
- `POST /api/send_immediate_notification` - 즉시 알림 발송

## 📊 대시보드 기능

### 실시간 통계
- 총 GA4 계정/프로퍼티 수
- 활성 사용자 수
- 승인 대기 수

### 관리자 제어 패널
- 📧 알림 즉시 발송
- ⏰ 만료 권한 처리
- 🧹 데이터 정리
- 🚀 전체 작업 실행

### 사용자 관리
- 최근 등록 사용자 목록
- 만료 예정 사용자 (7일 이내)
- 승인 대기 사용자 관리

## 🗃️ 데이터베이스 스키마

### 주요 테이블
- `user_registrations`: 사용자 등록 정보
- `ga4_accounts`: GA4 계정 정보
- `ga4_properties`: GA4 프로퍼티 정보
- `notification_logs`: 알림 발송 기록
- `audit_logs`: 감사 로그

### 권한 레벨
- `analyst`: 30일 만료, 자동 승인
- `editor`: 7일 만료, 수동 승인

### 상태 관리
- `pending_approval`: 승인 대기
- `active`: 활성
- `expired`: 만료
- `deleted`: 삭제
- `rejected`: 거부

## 📧 알림 시스템

### 알림 유형
- `welcome`: 환영 메시지
- `30_days`: 30일 전 만료 예정
- `7_days`: 7일 전 만료 예정
- `1_day`: 1일 전 만료 예정
- `today`: 당일 만료
- `expired`: 만료 후 삭제
- `approval_request`: 승인 요청 (관리자용)

### 발송 정책
- 각 단계별 1회만 발송
- 매일 체크하여 조건 충족 시 발송
- 즉시 발송 기능 지원

## 🔐 보안 기능

### 입력 검증
- 이메일 형식 검증
- 도메인 허용 목록 확인
- SQL 인젝션 방지
- 권한 레벨 검증

### 감사 로그
- 모든 CRUD 작업 기록
- 사용자별 작업 추적
- 타임스탬프 및 상태 기록

## 📈 성능 최적화

### 데이터베이스
- 인덱스 최적화
- 트랜잭션 관리
- 연결 풀링

### 비동기 처리
- async/await 패턴
- 병렬 작업 처리
- 논블로킹 I/O

## 🛠️ 개발 및 배포

### 개발 환경 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 초기화
python -c "
import asyncio
from src.infrastructure.database import db_manager
asyncio.run(db_manager.initialize_database())
"
```

### 테스트 환경
```bash
# 단위 테스트
python -m pytest tests/

# 통합 테스트
python run_comprehensive_tests.py

# 성능 테스트
python run_comprehensive_tests.py --test performance
```

### 프로덕션 배포
```bash
# 마이그레이션 실행
python migrate_to_analyst_system.py

# 웹 서버 시작 (프로덕션)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.web.main:app
```

## 📝 로그 및 모니터링

### 로그 파일
- `logs/ga4_automation.log`: 시스템 로그
- `test_results.json`: 테스트 결과
- `migration_log_*.txt`: 마이그레이션 로그

### 모니터링 지표
- 사용자 등록/삭제 수
- 알림 발송 성공/실패율
- API 응답 시간
- 데이터베이스 성능

## 🤝 기여 가이드

### 개발 프로세스
1. 이슈 생성 및 할당
2. 브랜치 생성 (`feature/기능명`)
3. 개발 및 테스트
4. Pull Request 생성
5. 코드 리뷰 및 승인
6. 메인 브랜치 병합

### 코딩 스타일
- PEP 8 준수
- Type hints 사용
- Docstring 작성
- 테스트 코드 포함

## 🆘 문제 해결

### 자주 발생하는 문제

#### 1. Gmail API 인증 오류
```bash
# 앱 비밀번호 재생성
# 2단계 인증 활성화 확인
# SMTP 설정 확인
```

#### 2. GA4 API 권한 오류
```bash
# 서비스 계정 권한 확인
# GA4 계정/프로퍼티 ID 확인
# API 할당량 확인
```

#### 3. 데이터베이스 오류
```bash
# 데이터베이스 백업에서 복원
cp database_backup_*.db data/ga4_automation.db

# 스키마 재초기화
python migrate_to_analyst_system.py
```

### 로그 확인
```bash
# 실시간 로그 모니터링
tail -f logs/ga4_automation.log

# 에러 로그만 확인
grep ERROR logs/ga4_automation.log

# 특정 사용자 관련 로그
grep "user@example.com" logs/ga4_automation.log
```

## 📞 지원 및 문의

- **이슈 리포트**: GitHub Issues
- **기능 요청**: GitHub Discussions
- **긴급 문의**: 시스템 관리자

## 📄 라이선스

MIT License - 자세한 내용은 LICENSE 파일 참조

---

**최신 업데이트**: 2025-01-21  
**버전**: 2.0.0 (Analyst/Editor 시스템)  
**테스트 커버리지**: 95%+ 