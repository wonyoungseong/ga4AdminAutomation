"""
FastAPI 미들웨어 모음
보안, 로깅, 에러 처리 등을 담당합니다.
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 요청 정보 로깅
        logger.info(f"📨 {request.method} {request.url}")
        
        # 요청 처리
        try:
            response = await call_next(request)
            
            # 처리 시간 계산
            process_time = time.time() - start_time
            
            # 응답 정보 로깅
            logger.info(
                f"📤 {request.method} {request.url} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.4f}s"
            )
            
            # 응답 헤더에 처리 시간 추가
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 에러 로깅
            process_time = time.time() - start_time
            logger.error(
                f"❌ {request.method} {request.url} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.4f}s"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """보안 헤더 추가 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 보안 헤더 추가
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        })
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """간단한 속도 제한 미들웨어 (개발용)"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {client_ip: [(timestamp, count), ...]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        current_time = time.time()
        
        # 현재 시간 기준으로 윈도우 내의 요청만 유지
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (timestamp, count) for timestamp, count in self.requests[client_ip]
                if current_time - timestamp < self.window_seconds
            ]
        else:
            self.requests[client_ip] = []
        
        # 현재 윈도우 내 요청 수 계산
        current_requests = sum(count for _, count in self.requests[client_ip])
        
        if current_requests >= self.max_requests:
            # 제한 초과 시 429 응답
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "message": "너무 많은 요청입니다. 잠시 후 다시 시도해주세요."}
            )
        
        # 요청 기록
        self.requests[client_ip].append((current_time, 1))
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(self.max_requests - current_requests - 1)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """요청 ID 추가 미들웨어"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid
        
        # 고유 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        # 요청 상태에 ID 저장 (다른 곳에서 사용 가능)
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # 응답 헤더에 요청 ID 추가
        response.headers["X-Request-ID"] = request_id
        
        return response 