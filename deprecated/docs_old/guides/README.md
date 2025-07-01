# GA4 사용자 관리 자동화 시스템

Google Analytics 4 (GA4) 속성의 사용자 권한을 자동으로 관리하는 시스템입니다.

## 🚀 주요 기능

### 1. 기본 사용자 관리
- ✅ **사용자 추가**: GA4 속성에 새로운 사용자 추가
- ✅ **사용자 제거**: 기존 사용자 권한 제거
- ✅ **사용자 목록 조회**: 현재 등록된 모든 사용자 확인
- ✅ **대화형 메뉴**: 사용자 친화적인 인터페이스

### 2. 날짜 기반 자동화 관리 ⭐ NEW
- ✅ **만료일 설정**: 사용자 추가 시 권한 만료일 지정 (예: 60일, 30일, 7일)
- ✅ **자동 알림**: 만료 예정 사용자에게 이메일 알림 발송
- ✅ **자동 제거**: 만료된 사용자 권한 자동 삭제
- ✅ **상태 리포트**: 사용자 권한 상태 및 만료 현황 리포트
- ✅ **스케줄 자동화**: 매일 자동으로 만료 확인 및 처리

### 3. 📧 Gmail/SMTP 알림 시스템 (NEW!)
- **환영 메일**: 사용자 등록 시 자동 발송
- **만료 경고 메일**: 7일, 3일, 1일 전 알림
- **삭제 알림 메일**: 권한 제거 후 알림
- **HTML 템플릿**: 아름다운 이메일 디자인

### 4. 🤖 자동화 스케줄러
- 매일 09:00: 만료 예정 사용자 알림
- 매일 00:00: 만료된 사용자 제거
- 주간 리포트 생성

## 📋 지원하는 권한 역할

| 역할 | 설명 |
|------|------|
| `viewer` | 보기 권한 |
| `analyst` | 분석가 권한 |
| `editor` | 편집자 권한 |
| `admin` | 관리자 권한 |

## 🛠️ 설치 및 설정

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. Service Account 설정
1. Google Cloud Console에서 Service Account 생성
2. Analytics Admin API 활성화
3. `ga4-automatio-797ec352f393.json` 파일 다운로드
4. GA4에서 Service Account를 Administrator 권한으로 추가

### 3. 설정 파일 구성

#### config.json
```json
{
  "account_id": "332818805",
  "property_id": "462884506",
  "new_user_email": "wonyoungseong@gmail.com",
  "new_user_role": "Analyst",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "sender_email": "your-email@gmail.com",
  "sender_password": "your-app-password"
}
```

### 4. Gmail SMTP 설정
1. Gmail 계정에서 2단계 인증 활성화
2. 앱 비밀번호 생성
3. `config.json`에 이메일과 앱 비밀번호 설정

## 🎯 사용 방법

### 기본 사용자 관리
```bash
python ga_api_automator.py
```

### 날짜 기반 자동화 관리
```bash
python user_management_with_dates.py
```

### 3. 자동화 스케줄러 실행
```bash
python automated_ga4_scheduler.py
```

## 📊 자동화 기능 상세

### 1. 기간 제한 사용자 추가
- 사용자 이메일, 역할, 만료일(일수) 설정
- GA4에 사용자 추가 + 로컬 데이터베이스에 만료 정보 저장
- 만료일 자동 계산 및 관리

### 2. 자동 알림 시스템
- **알림 시점**: 만료 60일, 30일, 7일, 1일 전
- **알림 방식**: 이메일 자동 발송
- **중복 방지**: 같은 날 중복 알림 방지
- **알림 로그**: 모든 알림 기록 저장

### 3. 자동 제거 시스템
- 만료된 사용자 자동 감지
- GA4에서 권한 자동 제거
- 제거 완료 알림 발송
- 데이터베이스 상태 업데이트

### 4. 스케줄 자동화
```
매일 09:00 - 만료 예정 사용자 알림 확인 및 발송
매일 00:00 - 만료된 사용자 자동 제거
매주 월요일 10:00 - 사용자 상태 리포트 생성
```

## 📈 상태 리포트 예시

```
=== GA4 사용자 상태 리포트 ===

📋 활성 사용자:
  ✅ 정상 admin@company.com (admin) - 만료: 무제한
  ✅ 정상 analyst@company.com (analyst) - 만료: 2025-08-15 (45일 남음)
  ⚠️ 곧 만료 temp@company.com (viewer) - 만료: 2025-07-01 (6일 남음)

⚠️ 7일 이내 만료 예정:
  temp@company.com (viewer) - 6일 후 만료
```

## 🗄️ 데이터베이스 구조

### ga4_users 테이블
- `email`: 사용자 이메일
- `property_id`: GA4 속성 ID
- `role`: 사용자 역할
- `granted_date`: 권한 부여일
- `expiry_date`: 만료일
- `status`: 상태 (active/expired)

### notification_logs 테이블
- `user_email`: 알림 대상 이메일
- `notification_type`: 알림 유형
- `sent_date`: 발송일
- `days_before_expiry`: 만료 전 일수
- `message_subject`: 메일 제목

## 🔧 고급 사용법

### 1. 커스텀 알림 일정 설정
```python
manager.check_expiring_users(notification_days=[90, 60, 30, 14, 7, 3, 1])
```

### 2. 특정 사용자 상태 확인
```python
manager.get_user_status_report(property_id)
```

### 3. 수동 만료 사용자 제거
```python
manager.remove_expired_users(property_id)
```

## ⚠️ 주의사항

1. **이메일 설정**: Gmail 사용 시 앱 비밀번호 필요
2. **Service Account 권한**: GA4에서 Administrator 권한 필수
3. **데이터베이스**: SQLite 파일 백업 권장
4. **스케줄 실행**: 서버에서 24시간 실행 필요

## 🔐 보안 고려사항

- Service Account 키 파일 보안 관리
- 이메일 비밀번호 환경변수 사용 권장
- 데이터베이스 파일 접근 권한 제한
- 정기적인 로그 모니터링

## 📞 문의 및 지원

추가 기능이나 문제가 있으면 언제든지 문의해주세요! 