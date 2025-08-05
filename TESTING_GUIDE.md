# Super Admin 테스트 가이드

## 수정 사항 요약
1. **SSL 프로토콜 오류 해결**: Next.js CSP에서 `upgrade-insecure-requests` 제거
2. **인증 상태 관리 개선**: 토큰 만료 확인 및 자동 갱신 로직 추가
3. **크로스 탭 동기화**: localStorage 이벤트 리스너로 탭 간 세션 동기화
4. **리디렉션 지연**: 토큰 갱신 완료 대기 후 리디렉션

## 테스트 시나리오 실행 방법

### 1. 기본 로그인 테스트
```
1. 브라우저에서 http://localhost:3000 접속
2. admin@test.com / admin123로 로그인
3. 대시보드 홈페이지 정상 로딩 확인
```

### 2. 세션 지속성 테스트
```
1. 로그인 상태에서 브라우저 새로고침 (F5)
2. 새 탭에서 http://localhost:3000/dashboard/users 직접 접근
3. 새 탭에서 http://localhost:3000/dashboard/permissions 직접 접근
4. 각 경우에서 로그인 페이지로 리디렉션되지 않는지 확인
```

### 3. 네비게이션 테스트
```
1. 사이드바 메뉴를 통해 다음 페이지들 순차 접근:
   - Users (사용자 관리)
   - Permissions (권한 관리) 
   - Service Accounts (서비스 계정)
   - GA4 Properties (GA4 속성)
   - Audit (감사 로그)
2. 각 페이지에서 데이터 로딩 및 오류 확인
```

### 4. 개발자 도구 디버깅

**콘솔에서 인증 상태 확인:**
```javascript
// 현재 토큰 확인
localStorage.getItem('auth_token')

// 토큰 만료 시간 확인  
localStorage.getItem('token_expiry')

// 현재 시간과 만료 시간 비교
const expiry = localStorage.getItem('token_expiry');
const now = Math.floor(Date.now() / 1000);
console.log(`Token expires at: ${expiry}, Current time: ${now}, Valid: ${now < expiry}`);

// API 요청 테스트
fetch('http://localhost:8000/api/enhanced-users/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
  }
}).then(r => r.json()).then(console.log);
```

**네트워크 탭에서 확인할 사항:**
- API 요청이 HTTP (not HTTPS)로 전송되는지
- 401 오류 시 자동 토큰 갱신 요청 발생하는지
- CORS 에러가 없는지

### 5. 예상 결과

**✅ 정상 동작:**
- 로그인 후 새 탭에서도 세션 유지
- 페이지 새로고침 후에도 로그인 상태 유지
- 모든 대시보드 페이지 정상 접근
- SSL 프로토콜 오류 해결

**❌ 만약 여전히 문제가 있다면:**
- 콘솔 오류 메시지 확인
- 네트워크 요청 상태 확인  
- 토큰 만료 시간 확인

## 테스트 결과 보고

테스트 완료 후 다음 정보를 제공해주세요:
1. 어떤 시나리오에서 로그인 페이지로 리디렉션되는지
2. 콘솔에 나타나는 오류 메시지
3. 네트워크 탭의 API 요청 상태
4. 토큰 만료 시간과 현재 시간 비교 결과