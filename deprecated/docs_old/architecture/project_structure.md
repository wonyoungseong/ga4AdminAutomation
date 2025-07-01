# GA4 자동화 시스템 프로젝트 구조

## 📁 디렉토리 구조

```
ga4AdminAutomation/
├── src/                        # 소스 코드
│   ├── core/                   # 핵심 비즈니스 로직
│   │   ├── email_validator.py  # 이메일 검증 시스템
│   │   ├── ga4_automation.py   # GA4 자동화 핵심 로직
│   │   └── gmail_service.py    # Gmail OAuth 서비스
│   ├── api/                    # API 엔드포인트
│   │   ├── invitation_api.py   # 초대 API
│   │   └── scheduler.py        # 스케줄러 API
│   └── infrastructure/         # 인프라 관련 코드
│       ├── diagnosis.py        # 진단 도구
│       ├── debug.py           # 디버깅 도구
│       └── check.py           # 검증 도구
├── tests/                      # 테스트 파일
│   ├── test_comprehensive_qa.py
│   ├── test_edge_cases.py
│   └── test_qa_report.py
├── docs/                       # 문서
│   ├── architecture/           # 아키텍처 문서
│   ├── guides/                 # 개발자 가이드
│   └── runbooks/              # 운영 매뉴얼
├── logs/                       # 로그 파일
├── data/                       # 데이터베이스 파일
├── archive/                    # 아카이브된 파일
├── config.json                 # 설정 파일
└── requirements.txt            # 의존성
```

## 🔧 핵심 컴포넌트

### 1. Core 모듈
- **EmailValidator**: GA4 API를 활용한 이메일 검증
- **GA4Automation**: GA4 사용자 관리 자동화
- **GmailService**: Gmail OAuth 이메일 발송

### 2. API 모듈  
- **InvitationAPI**: 사용자 초대 관리
- **Scheduler**: 자동화 스케줄링

### 3. Infrastructure 모듈
- **Diagnosis**: 시스템 진단 및 모니터링
- **Debug**: 디버깅 및 문제 해결
- **Check**: 시스템 검증

## 📋 규칙 준수사항

✅ **SOLID 원칙 적용**
- 단일 책임: 각 모듈이 명확한 역할 담당
- 개방-폐쇄: 확장 가능한 구조
- 의존성 역전: 인터페이스 기반 설계

✅ **Clean Architecture**
- 계층별 책임 분리
- 의존성 방향 제어
- 비즈니스 로직과 인프라 분리

✅ **명명 규칙**
- 파일명: snake_case
- 클래스명: PascalCase  
- 함수명: snake_case
- 상수: UPPER_SNAKE_CASE 