"""
Security middleware for GA4 Admin Automation System
"""

import time
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import hashlib
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware providing:
    - Rate limiting
    - IP blocking
    - Request fingerprinting
    - Brute force protection
    """
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=1)
        self.rate_limits = {
            '/api/auth/login': {'requests': 5, 'window': 300},  # 5 attempts per 5 minutes
            '/api/auth/register': {'requests': 3, 'window': 3600},  # 3 registrations per hour
            '/api/auth/refresh': {'requests': 10, 'window': 3600},  # 10 refreshes per hour
            'default': {'requests': 100, 'window': 3600}  # 100 requests per hour
        }
        
        # IP blocklist patterns (implement persistent storage in production)
        self.blocked_ips = set()
        self.suspicious_patterns = [
            'sqlmap', 'nikto', 'nmap', 'dirb', 'burp', 'havij',
            'union select', 'or 1=1', 'and 1=1', '../', '..\\',
            '<script', 'javascript:', 'onload=', 'onerror=',
            'eval(', 'document.cookie', 'alert('
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if await self._is_ip_blocked(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "IP_BLOCKED", "message": "IP address temporarily blocked"}
            )
        
        # Rate limiting
        if not await self._check_rate_limit(client_ip, request.url.path):
            await self._handle_rate_limit_exceeded(client_ip, request.url.path)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}
            )
        
        # Malicious pattern detection
        if await self._detect_malicious_patterns(request):
            await self._block_ip_temporarily(client_ip, reason="malicious_pattern")
            logger.warning(f"Malicious pattern detected from IP {client_ip}: {request.url}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "INVALID_REQUEST", "message": "Request blocked"}
            )
        
        # Add security headers
        response = await call_next(request)
        self._add_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP considering proxies"""
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else '127.0.0.1'
    
    async def _check_rate_limit(self, ip: str, path: str) -> bool:
        """Check if request is within rate limits"""
        try:
            # Get rate limit config for this path
            limit_config = self.rate_limits.get(path, self.rate_limits['default'])
            
            # Create Redis key
            window_start = int(time.time()) // limit_config['window'] * limit_config['window']
            key = f"rate_limit:{ip}:{path}:{window_start}"
            
            # Get current count
            current_count = await self._redis_get_int(key)
            
            if current_count >= limit_config['requests']:
                return False
            
            # Increment counter
            await self._redis_incr(key, limit_config['window'])
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow request on Redis failure
    
    async def _handle_rate_limit_exceeded(self, ip: str, path: str):
        """Handle rate limit exceeded"""
        # Track repeated violations
        violation_key = f"violations:{ip}"
        violations = await self._redis_get_int(violation_key)
        violations += 1
        await self._redis_set(violation_key, violations, 3600)  # Track for 1 hour
        
        # Block IP after multiple violations
        if violations >= 5:
            await self._block_ip_temporarily(ip, reason="repeated_rate_limit_violations")
    
    async def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        try:
            blocked_until = await self._redis_get(f"blocked_ip:{ip}")
            if blocked_until:
                if float(blocked_until) > time.time():
                    return True
                else:
                    # Remove expired block
                    await self._redis_delete(f"blocked_ip:{ip}")
            return False
        except Exception as e:
            logger.error(f"Error checking IP block status: {e}")
            return False
    
    async def _block_ip_temporarily(self, ip: str, duration: int = 3600, reason: str = "security_violation"):
        """Block IP temporarily"""
        try:
            block_until = time.time() + duration
            await self._redis_set(f"blocked_ip:{ip}", str(block_until), duration)
            
            logger.warning(f"IP {ip} blocked for {duration} seconds. Reason: {reason}")
            
            # Log security event
            security_event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "ip_blocked",
                "ip_address": ip,
                "reason": reason,
                "duration": duration
            }
            await self._log_security_event(security_event)
            
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
    
    async def _detect_malicious_patterns(self, request: Request) -> bool:
        """Detect malicious patterns in request"""
        try:
            # Check URL path
            path = str(request.url.path).lower()
            query = str(request.url.query).lower()
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if pattern in path or pattern in query:
                    return True
            
            # Check headers for suspicious content
            user_agent = request.headers.get('User-Agent', '').lower()
            for pattern in ['sqlmap', 'nikto', 'nmap', 'burp']:
                if pattern in user_agent:
                    return True
            
            # Check request body for POST requests
            if request.method == "POST":
                try:
                    body = await request.body()
                    if body:
                        body_str = body.decode('utf-8', errors='ignore').lower()
                        for pattern in self.suspicious_patterns:
                            if pattern in body_str:
                                return True
                except Exception:
                    pass  # Skip body check if there's an error
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting malicious patterns: {e}")
            return False
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        response.headers.update({
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        })
    
    async def _redis_get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        try:
            value = self.redis_client.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def _redis_get_int(self, key: str) -> int:
        """Get integer value from Redis"""
        try:
            value = await self._redis_get(key)
            return int(value) if value else 0
        except Exception:
            return 0
    
    async def _redis_set(self, key: str, value: str, ttl: int):
        """Set value in Redis with TTL"""
        try:
            self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
    
    async def _redis_incr(self, key: str, ttl: int):
        """Increment Redis key and set TTL"""
        try:
            pipeline = self.redis_client.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, ttl)
            pipeline.execute()
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
    
    async def _redis_delete(self, key: str):
        """Delete key from Redis"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
    
    async def _log_security_event(self, event: Dict):
        """Log security event for monitoring"""
        try:
            event_key = f"security_events:{int(time.time())}"
            await self._redis_set(event_key, json.dumps(event), 86400)  # Keep for 24 hours
            logger.info(f"Security event logged: {event['event_type']}")
        except Exception as e:
            logger.error(f"Error logging security event: {e}")


class BruteForceProtection:
    """Brute force protection for authentication endpoints"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=2)
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.attempt_window = 300    # 5 minutes
    
    async def check_auth_attempts(self, identifier: str) -> bool:
        """Check if authentication is allowed for identifier (email or IP)"""
        try:
            # Check if currently locked out
            lockout_key = f"auth_lockout:{identifier}"
            lockout_until = await self._get_value(lockout_key)
            
            if lockout_until and float(lockout_until) > time.time():
                return False
            
            # Check attempts in current window
            window_start = int(time.time()) // self.attempt_window * self.attempt_window
            attempts_key = f"auth_attempts:{identifier}:{window_start}"
            attempts = await self._get_int_value(attempts_key)
            
            return attempts < self.max_attempts
            
        except Exception as e:
            logger.error(f"Error checking auth attempts: {e}")
            return True  # Allow on error
    
    async def record_failed_attempt(self, identifier: str):
        """Record a failed authentication attempt"""
        try:
            window_start = int(time.time()) // self.attempt_window * self.attempt_window
            attempts_key = f"auth_attempts:{identifier}:{window_start}"
            
            # Increment attempts
            pipeline = self.redis_client.pipeline()
            pipeline.incr(attempts_key)
            pipeline.expire(attempts_key, self.attempt_window)
            results = pipeline.execute()
            
            current_attempts = results[0]
            
            # Lock out if max attempts reached
            if current_attempts >= self.max_attempts:
                lockout_key = f"auth_lockout:{identifier}"
                lockout_until = time.time() + self.lockout_duration
                self.redis_client.setex(lockout_key, self.lockout_duration, str(lockout_until))
                
                logger.warning(f"Authentication lockout for {identifier}: {current_attempts} failed attempts")
                
                return True  # Locked out
            
            return False  # Not locked out yet
            
        except Exception as e:
            logger.error(f"Error recording failed attempt: {e}")
            return False
    
    async def record_successful_auth(self, identifier: str):
        """Record successful authentication (clears attempts)"""
        try:
            # Remove current window attempts
            window_start = int(time.time()) // self.attempt_window * self.attempt_window
            attempts_key = f"auth_attempts:{identifier}:{window_start}"
            self.redis_client.delete(attempts_key)
            
            # Remove lockout if exists
            lockout_key = f"auth_lockout:{identifier}"
            self.redis_client.delete(lockout_key)
            
        except Exception as e:
            logger.error(f"Error recording successful auth: {e}")
    
    async def _get_value(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        try:
            value = self.redis_client.get(key)
            return value.decode('utf-8') if value else None
        except Exception:
            return None
    
    async def _get_int_value(self, key: str) -> int:
        """Get integer value from Redis"""
        try:
            value = await self._get_value(key)
            return int(value) if value else 0
        except Exception:
            return 0


class TokenBlacklist:
    """JWT token blacklist for secure logout"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=3)
    
    async def blacklist_token(self, token: str, expires_at: datetime):
        """Add token to blacklist"""
        try:
            # Calculate TTL (time until token expires)
            ttl = max(int((expires_at - datetime.utcnow()).total_seconds()), 0)
            
            if ttl > 0:
                # Hash token for privacy
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                key = f"blacklisted_token:{token_hash}"
                self.redis_client.setex(key, ttl, "1")
                
                logger.info(f"Token blacklisted with TTL: {ttl} seconds")
                
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"blacklisted_token:{token_hash}"
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False
    
    async def clear_expired_tokens(self):
        """Clean up expired tokens (Redis handles this automatically with TTL)"""
        # Redis automatically removes expired keys
        pass