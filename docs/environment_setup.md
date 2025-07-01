# 환경 변수 설정 가이드

## Supabase 프로젝트 생성 후 설정할 환경 변수

프로젝트 루트에 `.env` 파일을 생성하고 아래 변수들을 설정하세요:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Database Configuration (if needed for direct connections)
DATABASE_URL=your_database_connection_string_here

# Google API Configuration (will be added later)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# Application Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=info

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

## Supabase API 키 획득 방법

1. Supabase 프로젝트 대시보드로 이동
2. 왼쪽 메뉴에서 **Settings** > **API** 클릭
3. 다음 정보를 복사:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** 키 → `SUPABASE_ANON_KEY`
   - **service_role secret** 키 → `SUPABASE_SERVICE_ROLE_KEY`

## 보안 주의사항

- `.env` 파일은 절대 Git에 커밋하지 마세요
- Service Role 키는 매우 중요하니 안전하게 보관하세요
- 프로덕션 환경에서는 다른 키를 사용하세요 