# GA4 권한 관리 시스템 포괄적 테스트 시나리오

작성일: 2025-01-21  
프로젝트: GA4 Admin Automation  
기반: 답변 완료된 요구사항 분석  

## 📋 테스트 환경 설정

### 테스트 데이터
- **관리자 이메일**: seongwonyoung0311@gmail.com
- **GA4 계정**: account_id(332818805), property_id(462884506)
- **테스트 사용자 목록**:
  - ✅ 성공 예상: wonyoungseong@gmail.com, wonyoung.seong@conentrix.com, wonyoung.seong@amorepacific.com, seongwonyoung0311@gmail.com
  - ❌ 실패 예상: salboli@naver.com, demotest@gmail.com

### 권한 정책
- **Analyst**: 30일 만료 + 자동 삭제 (향후 설정 가능하도록 개발 예정)
- **Editor**: 7일 만료 + 자동 삭제 (수동 승인 필요)

### 알림 정책
- 매일 체크하여 30일/7일/1일 전 각각 1회 발송
- 만료 당일 알림 + 삭제 후 삭제 알림
- 테스트 시 즉시 발송 기능 사용

---

## 🎯 테스트 시나리오

### 1. 시스템 초기화 및 권한 레벨 변경 테스트

#### 1.1 권한 레벨 시스템 변경
**목적**: viewer/editor → analyst/editor로 시스템 변경
**실행 방법**:
```bash
# 마이그레이션 실행
python migrate_to_analyst_system.py

# 변경 사항 확인
python -c "
import asyncio
from src.infrastructure.database import db_manager
async def check():
    result = await db_manager.execute_query('SELECT DISTINCT 권한 FROM user_registrations')
    print([r['권한'] for r in result])
asyncio.run(check())
"
```

**예상 결과**:
- 기존 viewer 권한이 모두 analyst로 변경
- 데이터베이스 스키마 CHECK 제약 조건 업데이트
- 백업 파일 생성 및 마이그레이션 로그 생성

#### 1.2 이메일 검증 시스템 테스트
**목적**: 회사 도메인 이메일 지원 확인
**실행 방법**:
```python
from src.services.email_validator import email_validator

# 성공 예상 테스트
test_emails = [
    'wonyoungseong@gmail.com',
    'wonyoung.seong@conentrix.com', 
    'wonyoung.seong@amorepacific.com',
    'seongwonyoung0311@gmail.com'
]

for email in test_emails:
    result = email_validator.validate_email(email)
    print(f"{email}: {'✅' if result.is_valid else '❌'} {'(회사)' if result.is_company_email else ''}")

# 실패 예상 테스트
fail_emails = ['salboli@naver.com', 'demotest@gmail.com']
for email in fail_emails:
    result = email_validator.validate_email(email)
    print(f"{email}: {'❌ 예상대로 실패' if not result.is_valid else '⚠️ 예상과 다름'}")
```

---

### 2. 권한 추가 시나리오

#### 2.1 Analyst 권한 추가 (자동 승인)
**테스트 단계**:
1. **API 호출**:
   ```bash
   curl -X POST http://localhost:8000/api/add_user \
     -H "Content-Type: application/json" \
     -d '{
       "email": "wonyoungseong@gmail.com",
       "property_id": "462884506",
       "role": "analyst",
       "requester": "seongwonyoung0311@gmail.com"
     }'
   ```

2. **데이터베이스 확인**:
   ```sql
   SELECT * FROM user_registrations 
   WHERE 등록_계정 = 'wonyoungseong@gmail.com' 
   ORDER BY created_at DESC LIMIT 1;
   ```

3. **GA4 API 연동 확인**: 실제 GA4에서 권한 부여 여부 확인

**예상 결과**:
- status: 'active' (자동 승인)
- approval_required: false
- 권한: 'analyst'
- 종료일: 30일 후
- 환영 이메일 발송

#### 2.2 Editor 권한 추가 (승인 대기)
**테스트 단계**:
1. **API 호출**:
   ```bash
   curl -X POST http://localhost:8000/api/add_user \
     -H "Content-Type: application/json" \
     -d '{
       "email": "wonyoung.seong@conentrix.com",
       "property_id": "462884506", 
       "role": "editor",
       "requester": "seongwonyoung0311@gmail.com"
     }'
   ```

2. **승인 대기 상태 확인**:
   ```sql
   SELECT status, approval_required FROM user_registrations 
   WHERE 등록_계정 = 'wonyoung.seong@conentrix.com';
   ```

**예상 결과**:
- status: 'pending_approval'
- approval_required: true
- 권한: 'editor'
- 종료일: 7일 후
- 승인 요청 이메일 발송

#### 2.3 잘못된 이메일 권한 추가 시도
**테스트 단계**:
```bash
curl -X POST http://localhost:8000/api/add_user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "salboli@naver.com",
    "property_id": "462884506",
    "role": "analyst",
    "requester": "seongwonyoung0311@gmail.com"
  }'
```

**예상 결과**:
- HTTP 400 Bad Request
- 이메일 검증 실패 메시지
- 데이터베이스에 등록되지 않음

---

### 3. 권한 업데이트 시나리오

#### 3.1 권한 레벨 변경
**목적**: 기존 사용자의 analyst → editor 변경
**테스트 단계**:
1. **기존 사용자 확인**:
   ```sql
   SELECT * FROM user_registrations 
   WHERE 등록_계정 = 'wonyoungseong@gmail.com' AND status = 'active';
   ```

2. **권한 업데이트**:
   ```bash
   curl -X PUT http://localhost:8000/api/update_user \
     -H "Content-Type: application/json" \
     -d '{
       "email": "wonyoungseong@gmail.com",
       "property_id": "462884506",
       "new_role": "editor"
     }'
   ```

3. **변경 사항 확인**:
   - 데이터베이스에서 권한 변경 확인
   - 종료일이 7일로 변경되었는지 확인
   - 승인이 필요한 상태로 변경되었는지 확인

#### 3.2 만료일 연장
**테스트 단계**:
1. **연장 요청**:
   ```bash
   curl -X POST http://localhost:8000/api/extend_permission \
     -H "Content-Type: application/json" \
     -d '{
       "email": "wonyoungseong@gmail.com",
       "property_id": "462884506",
       "extension_days": 30
     }'
   ```

2. **연장 결과 확인**:
   ```sql
   SELECT 종료일, 연장_횟수, 최근_연장일 
   FROM user_registrations 
   WHERE 등록_계정 = 'wonyoungseong@gmail.com';
   ```

---

### 4. 권한 삭제 시나리오

#### 4.1 수동 권한 삭제
**테스트 단계**:
1. **삭제 요청**:
   ```bash
   curl -X DELETE http://localhost:8000/api/remove_user \
     -H "Content-Type: application/json" \
     -d '{
       "email": "wonyoung.seong@amorepacific.com",
       "property_id": "462884506"
     }'
   ```

2. **삭제 확인**:
   - 데이터베이스에서 status가 'deleted'로 변경
   - GA4에서 권한 제거 확인
   - 삭제 알림 이메일 발송 확인

#### 4.2 만료된 권한 자동 삭제
**테스트 준비**:
```sql
-- 만료된 테스트 데이터 생성
INSERT INTO user_registrations 
(신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status, ga4_registered)
VALUES 
('seongwonyoung0311@gmail.com', 'expired_test@gmail.com', '462884506', 
 'analyst', datetime('now', '-32 days'), datetime('now', '-2 days'), 'active', 1);
```

**자동 삭제 실행**:
```bash
# 스케줄러 수동 실행
curl -X POST http://localhost:8000/api/trigger_scheduler \
  -H "Content-Type: application/json" \
  -d '{"task_type": "expired"}'
```

**결과 확인**:
- 만료된 사용자가 자동으로 삭제됨
- status가 'deleted'로 변경
- 만료 알림 및 삭제 알림 발송

---

### 5. 알림 시스템 시나리오

#### 5.1 만료 예정 알림 테스트
**테스트 데이터 생성**:
```sql
-- 30일 전 알림 테스트
INSERT INTO user_registrations 
(신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status, ga4_registered)
VALUES 
('seongwonyoung0311@gmail.com', 'test_30days@gmail.com', '462884506', 
 'analyst', datetime('now'), datetime('now', '+30 days'), 'active', 1);

-- 7일 전 알림 테스트  
INSERT INTO user_registrations 
(신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status, ga4_registered)
VALUES 
('seongwonyoung0311@gmail.com', 'test_7days@gmail.com', '462884506', 
 'analyst', datetime('now'), datetime('now', '+7 days'), 'active', 1);

-- 1일 전 알림 테스트
INSERT INTO user_registrations 
(신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status, ga4_registered)
VALUES 
('seongwonyoung0311@gmail.com', 'test_1day@gmail.com', '462884506', 
 'analyst', datetime('now'), datetime('now', '+1 days'), 'active', 1);

-- 당일 알림 테스트
INSERT INTO user_registrations 
(신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status, ga4_registered)
VALUES 
('seongwonyoung0311@gmail.com', 'test_today@gmail.com', '462884506', 
 'analyst', datetime('now'), datetime('now'), 'active', 1);
```

**알림 발송 테스트**:
```bash
# 즉시 알림 발송
curl -X POST http://localhost:8000/api/trigger_scheduler \
  -H "Content-Type: application/json" \
  -d '{"task_type": "notifications"}'
```

**결과 확인**:
- 각 단계별 알림 이메일 발송 확인
- notification_logs 테이블에 기록 확인
- 중복 발송 방지 로직 확인

#### 5.2 즉시 알림 발송 기능 테스트
**대시보드에서 수동 실행**:
1. http://localhost:8000/dashboard 접속
2. "📧 알림 즉시 발송" 버튼 클릭
3. 결과 메시지 확인

**API 직접 호출**:
```bash
curl -X POST http://localhost:8000/api/send_immediate_notification \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seongwonyoung0311@gmail.com",
    "notification_type": "test",
    "message": "테스트 알림입니다."
  }'
```

---

### 6. UI/UX 검증 시나리오

#### 6.1 대시보드 실시간 업데이트 확인
**테스트 순서**:
1. **대시보드 접속**: http://localhost:8000/dashboard
2. **초기 통계 확인**: 총 계정, 프로퍼티, 활성 사용자, 승인 대기 수
3. **새 사용자 추가**: API 또는 웹 폼을 통해 사용자 추가
4. **대시보드 새로고침**: 통계가 업데이트되었는지 확인
5. **실시간 데이터 확인**: 최근 등록 사용자, 만료 예정 사용자 목록

#### 6.2 권한 레벨 표시 확인
**확인 사항**:
- 권한 표시가 "Analyst", "Editor"로 정확히 표시되는지
- 권한별 색상 구분이 적절한지 (Analyst: 파란색, Editor: 빨간색)
- 상태 표시가 정확한지 (활성, 승인 대기, 만료, 삭제)

#### 6.3 관리자 제어 패널 테스트
**테스트 기능**:
1. **📧 알림 즉시 발송** 버튼 클릭
2. **⏰ 만료 권한 처리** 버튼 클릭  
3. **🧹 데이터 정리** 버튼 클릭
4. **🚀 전체 작업 실행** 버튼 클릭

**확인 사항**:
- 버튼 클릭 시 로딩 상태 표시
- 작업 완료 후 결과 메시지 표시
- 3초 후 페이지 자동 새로고침

#### 6.4 승인 대기 사용자 관리
**테스트 순서**:
1. Editor 권한 사용자 추가 (승인 대기 상태)
2. 대시보드에서 승인 대기 목록 확인
3. "승인" 버튼 클릭하여 승인 처리
4. "거부" 버튼 클릭하여 거부 처리
5. 상태 변경 확인

---

### 7. 데이터베이스 연동 시나리오

#### 7.1 CRUD 작업 무결성 테스트
**Create 테스트**:
```python
# 사용자 등록 생성
registration_data = {
    '신청자': 'seongwonyoung0311@gmail.com',
    '등록_계정': 'crud_test@gmail.com', 
    'property_id': '462884506',
    '권한': 'analyst',
    '신청일': datetime.now(),
    '종료일': datetime.now() + timedelta(days=30),
    'status': 'active'
}
```

**Read 테스트**:
```sql
SELECT * FROM user_registrations WHERE 등록_계정 = 'crud_test@gmail.com';
```

**Update 테스트**:
```sql
UPDATE user_registrations 
SET 권한 = 'editor', 종료일 = datetime('now', '+7 days')
WHERE 등록_계정 = 'crud_test@gmail.com';
```

**Delete 테스트**:
```sql
UPDATE user_registrations 
SET status = 'deleted', updated_at = datetime('now')
WHERE 등록_계정 = 'crud_test@gmail.com';
```

#### 7.2 트랜잭션 무결성 테스트
**실패 시나리오 테스트**:
```python
# 의도적으로 실패하는 트랜잭션
try:
    # 1. 사용자 등록
    # 2. GA4 API 호출 (실패 시뮬레이션)
    # 3. 롤백 확인
    pass
except Exception:
    # 롤백이 정상적으로 수행되었는지 확인
    pass
```

#### 7.3 데이터 일관성 검증
**검증 쿼리**:
```sql
-- 중복 등록 확인
SELECT 등록_계정, property_id, COUNT(*) 
FROM user_registrations 
WHERE status = 'active'
GROUP BY 등록_계정, property_id 
HAVING COUNT(*) > 1;

-- 잘못된 권한 확인
SELECT * FROM user_registrations 
WHERE 권한 NOT IN ('analyst', 'editor');

-- 잘못된 상태 확인
SELECT * FROM user_registrations 
WHERE status NOT IN ('pending_approval', 'active', 'expired', 'rejected', 'deleted');

-- 만료일 이상 확인
SELECT * FROM user_registrations 
WHERE 종료일 < 신청일;
```

---

### 8. 성능 및 안정성 시나리오

#### 8.1 대량 데이터 처리 테스트
**테스트 데이터 생성**:
```python
# 100개의 테스트 등록 생성
import asyncio
from datetime import datetime, timedelta

async def create_bulk_test_data():
    for i in range(100):
        await db_manager.execute_update(
            """INSERT INTO user_registrations 
               (신청자, 등록_계정, property_id, 권한, 신청일, 종료일, status)
               VALUES (?, ?, ?, 'analyst', ?, ?, 'active')""",
            ('admin', f'bulk_test_{i}@gmail.com', '462884506', 
             datetime.now(), datetime.now() + timedelta(days=30))
        )
```

**성능 측정**:
- 처리 시간 10초 이내 목표
- 메모리 사용량 모니터링
- 데이터베이스 락 발생 여부 확인

#### 8.2 동시성 테스트
**동시 요청 시뮬레이션**:
```python
import asyncio
import aiohttp

async def concurrent_requests():
    tasks = []
    for i in range(10):
        task = aiohttp.post('http://localhost:8000/api/add_user', json={
            'email': f'concurrent_test_{i}@gmail.com',
            'property_id': '462884506',
            'role': 'analyst'
        })
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

#### 8.3 메모리 누수 테스트
**장시간 실행 테스트**:
```bash
# 1시간 동안 반복 요청
for i in {1..3600}; do
    curl -X GET http://localhost:8000/api/stats
    sleep 1
done
```

**메모리 모니터링**:
```bash
# 메모리 사용량 모니터링
while true; do
    ps aux | grep python | grep main.py
    sleep 60
done
```

---

### 9. 보안 및 권한 시나리오

#### 9.1 SQL 인젝션 방지 테스트
**악성 입력 테스트**:
```bash
# SQL 인젝션 시도
curl -X POST http://localhost:8000/api/add_user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com; DROP TABLE user_registrations; --",
    "property_id": "462884506",
    "role": "analyst"
  }'
```

**예상 결과**:
- 이메일 검증에서 실패
- 데이터베이스 테이블이 삭제되지 않음
- 적절한 오류 메시지 반환

#### 9.2 권한 레벨 검증 테스트
**지원하지 않는 권한 테스트**:
```bash
curl -X POST http://localhost:8000/api/add_user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com",
    "property_id": "462884506", 
    "role": "admin"
  }'
```

**예상 결과**:
- HTTP 400 Bad Request
- "지원하지 않는 권한 레벨" 오류 메시지
- 데이터베이스에 등록되지 않음

#### 9.3 입력 데이터 검증 테스트
**필수 필드 누락 테스트**:
```bash
curl -X POST http://localhost:8000/api/add_user \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com"
  }'
```

**잘못된 데이터 타입 테스트**:
```bash
curl -X POST http://localhost:8000/api/add_user \
  -H "Content-Type: application/json" \
  -d '{
    "email": 123,
    "property_id": null,
    "role": ["analyst"]
  }'
```

---

### 10. 통합 테스트 시나리오

#### 10.1 전체 워크플로우 테스트
**시나리오**: 사용자 등록부터 만료까지 전체 과정
1. **사용자 등록**: Analyst 권한으로 등록
2. **환영 이메일**: 등록 완료 알림 확인
3. **권한 확인**: GA4에서 실제 권한 부여 확인
4. **만료 예정 알림**: 30일, 7일, 1일 전 알림 확인
5. **당일 알림**: 만료 당일 알림 확인
6. **자동 삭제**: 만료 후 자동 삭제 확인
7. **삭제 알림**: 삭제 완료 알림 확인

#### 10.2 Editor 승인 워크플로우 테스트
**시나리오**: Editor 권한 요청부터 승인까지
1. **Editor 권한 요청**: 승인 대기 상태로 등록
2. **승인 요청 알림**: 관리자에게 승인 요청 이메일
3. **대시보드 확인**: 승인 대기 목록에 표시
4. **승인 처리**: 관리자가 승인 버튼 클릭
5. **승인 완료 알림**: 사용자에게 승인 완료 이메일
6. **GA4 권한 부여**: 실제 Editor 권한 부여 확인
7. **7일 후 자동 삭제**: Editor 권한 만료 처리

---

## 🚀 테스트 실행 방법

### 1. 시스템 마이그레이션
```bash
# viewer → analyst 시스템 마이그레이션
python migrate_to_analyst_system.py
```

### 2. 포괄적 테스트 실행
```bash
# 전체 테스트 실행
python run_comprehensive_tests.py

# 특정 테스트만 실행
python run_comprehensive_tests.py --test email
python run_comprehensive_tests.py --test notification

# 테스트 목록 확인
python run_comprehensive_tests.py --list

# 도움말
python run_comprehensive_tests.py --help
```

### 3. 웹 서버 시작
```bash
# 웹 서버 실행
python src/web/main.py

# 대시보드 접속
open http://localhost:8000/dashboard
```

### 4. 스케줄러 수동 실행
```bash
# 알림 즉시 발송
curl -X POST http://localhost:8000/api/trigger_scheduler \
  -d '{"task_type": "notifications"}'

# 만료 권한 처리
curl -X POST http://localhost:8000/api/trigger_scheduler \
  -d '{"task_type": "expired"}'

# 전체 작업 실행
curl -X POST http://localhost:8000/api/trigger_scheduler \
  -d '{"task_type": "all"}'
```

---

## 📊 테스트 결과 확인

### 1. 로그 파일 확인
```bash
# 시스템 로그
tail -f logs/ga4_automation.log

# 테스트 결과
cat test_results.json

# 마이그레이션 로그
cat migration_log_*.txt
```

### 2. 데이터베이스 확인
```sql
-- 사용자 등록 현황
SELECT 권한, status, COUNT(*) as count 
FROM user_registrations 
GROUP BY 권한, status;

-- 알림 발송 현황
SELECT notification_type, COUNT(*) as count 
FROM notification_logs 
GROUP BY notification_type;

-- 감사 로그 확인
SELECT action_type, COUNT(*) as count 
FROM audit_logs 
GROUP BY action_type;
```

### 3. 시스템 통계 확인
```bash
# API를 통한 통계 확인
curl http://localhost:8000/api/stats
```

---

## 🎯 성공 기준

### 기능적 요구사항
- ✅ 권한 추가/수정/삭제 정상 작동
- ✅ Analyst/Editor 권한 시스템 정상 작동
- ✅ 회사 도메인 이메일 지원
- ✅ 자동 만료 처리 (Editor/Analyst 모두 삭제)
- ✅ 30/7/1일 전, 당일, 삭제 알림 발송
- ✅ UI/UX 실시간 업데이트
- ✅ 수동 스케줄러 실행 기능

### 비기능적 요구사항  
- ✅ 성능: 100개 데이터 처리 10초 이내
- ✅ 안정성: 24시간 연속 실행 가능
- ✅ 보안: SQL 인젝션 방지, 입력 검증
- ✅ 데이터 무결성: 트랜잭션 롤백 정상 작동
- ✅ 로깅: 모든 작업 감사 로그 기록

### 사용자 경험
- ✅ 직관적인 대시보드 인터페이스
- ✅ 실시간 상태 업데이트
- ✅ 명확한 오류 메시지
- ✅ 적절한 알림 시스템

---

## 📝 테스트 완료 체크리스트

### 시스템 설정
- [ ] 마이그레이션 완료 (viewer → analyst)
- [ ] 이메일 검증 시스템 작동
- [ ] 회사 도메인 지원 확인

### 권한 관리
- [ ] Analyst 권한 추가 (자동 승인)
- [ ] Editor 권한 추가 (수동 승인)
- [ ] 권한 업데이트 및 연장
- [ ] 수동 권한 삭제
- [ ] 자동 만료 처리

### 알림 시스템
- [ ] 30일 전 알림
- [ ] 7일 전 알림  
- [ ] 1일 전 알림
- [ ] 당일 알림
- [ ] 삭제 후 알림
- [ ] 즉시 발송 기능

### UI/UX
- [ ] 대시보드 실시간 업데이트
- [ ] 권한 레벨 정확한 표시
- [ ] 승인 대기 관리 기능
- [ ] 수동 스케줄러 실행 버튼

### 데이터베이스
- [ ] CRUD 작업 무결성
- [ ] 트랜잭션 롤백
- [ ] 데이터 일관성 검증
- [ ] 감사 로그 기록

### 성능 및 보안
- [ ] 대량 데이터 처리 성능
- [ ] 동시성 처리
- [ ] SQL 인젝션 방지
- [ ] 입력 데이터 검증

---

**테스트 완료 후 이 문서와 함께 test_results.json 파일을 확인하여 모든 테스트가 성공했는지 검증하세요.** 