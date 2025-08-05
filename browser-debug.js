// 브라우저 콘솔에서 실행할 디버깅 스크립트
// http://localhost:3000에서 F12 -> Console에서 실행

console.log("=== GA4 Admin 인증 디버깅 시작 ===");

// 1. 현재 인증 상태 확인
function checkAuthState() {
    console.log("\n1. 인증 상태 확인:");
    const token = localStorage.getItem('auth_token');
    const refreshToken = localStorage.getItem('refresh_token');
    const expiry = localStorage.getItem('token_expiry');
    
    console.log("토큰 존재:", !!token);
    console.log("리프레시 토큰 존재:", !!refreshToken);
    
    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const now = Math.floor(Date.now() / 1000);
            console.log("토큰 만료 시간:", new Date(payload.exp * 1000));
            console.log("현재 시간:", new Date());
            console.log("토큰 유효:", now < payload.exp);
            console.log("사용자 정보:", payload);
        } catch (e) {
            console.error("토큰 파싱 오류:", e);
        }
    }
}

// 2. 로그인 테스트
async function testLogin() {
    console.log("\n2. 로그인 테스트:");
    try {
        const response = await fetch('http://localhost:8000/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: 'admin@test.com',
                password: 'admin123'
            })
        });
        
        const data = await response.json();
        console.log("로그인 응답:", response.status, data);
        
        if (response.ok) {
            localStorage.setItem('auth_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            const payload = JSON.parse(atob(data.access_token.split('.')[1]));
            localStorage.setItem('token_expiry', payload.exp.toString());
            console.log("✅ 로그인 성공, 토큰 저장됨");
        }
    } catch (error) {
        console.error("❌ 로그인 오류:", error);
    }
}

// 3. API 호출 테스트
async function testAPI(endpoint) {
    console.log(`\n3. API 테스트: ${endpoint}`);
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        console.error("❌ 토큰이 없습니다");
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:8000${endpoint}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log("응답 상태:", response.status);
        console.log("응답 헤더:", Object.fromEntries(response.headers.entries()));
        
        const data = await response.json();
        console.log("응답 데이터:", data);
        
        return { status: response.status, data };
    } catch (error) {
        console.error("❌ API 오류:", error);
        return { error: error.message };
    }
}

// 4. 전체 테스트 실행
async function runFullTest() {
    console.clear();
    console.log("=== GA4 Admin 전체 테스트 시작 ===");
    
    checkAuthState();
    
    // 로그인이 필요한 경우
    const token = localStorage.getItem('auth_token');
    if (!token) {
        console.log("\n토큰이 없어서 로그인 시도...");
        await testLogin();
    }
    
    // API 테스트
    const endpoints = [
        '/api/auth/me',
        '/api/enhanced-users/',
        '/api/permissions/',
        '/api/service-accounts',
        '/api/ga4-properties'
    ];
    
    for (const endpoint of endpoints) {
        await testAPI(endpoint);
        await new Promise(resolve => setTimeout(resolve, 100)); // 100ms 대기
    }
    
    console.log("\n=== 테스트 완료 ===");
}

// 스크립트 자동 실행
runFullTest();

// 사용법 안내
console.log(`
사용법:
- checkAuthState(): 현재 인증 상태 확인
- testLogin(): 로그인 테스트
- testAPI('/api/permissions/'): 특정 API 테스트
- runFullTest(): 전체 테스트 실행

문제 진단:
1. 브라우저에서 http://localhost:3000 접속
2. F12 -> Console 탭
3. 이 스크립트 전체를 복사해서 붙여넣기
4. 결과 확인 후 permissions 페이지로 이동해서 오류 확인
`);