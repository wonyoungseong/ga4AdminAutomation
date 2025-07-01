#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 GA4 웹 시스템 테스트 서버
===============================

실제 GA4 권한 관리 시스템의 기능을 테스트하기 위한 서버입니다.
"""

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Optional
import uvicorn
import sqlite3
import json
from datetime import datetime, timedelta

app = FastAPI(title="GA4 권한 관리 시스템 테스트")

# 간단한 메모리 데이터베이스
TEST_USERS = [
    {
        "id": 1,
        "신청자": "테스트담당자1",
        "등록_계정": "existing.user@example.com",
        "property_id": "462884506",
        "권한": "analyst",
        "status": "active",
        "신청일": "2025-06-01",
        "종료일": "2025-07-01"
    },
    {
        "id": 2,
        "신청자": "테스트담당자2", 
        "등록_계정": "test.user@example.com",
        "property_id": "462884506",
        "권한": "viewer",
        "status": "active",
        "신청일": "2025-06-15",
        "종료일": "2025-07-15"
    }
]

PROPERTY_DATA = [
    {
        "property_id": "462884506",
        "property_name": "아모레퍼시픽 웹사이트",
        "account_name": "아모레퍼시픽",
        "account_id": "123456789"
    }
]

@app.get("/", response_class=HTMLResponse)
async def home():
    """메인 대시보드"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <title>GA4 권한 관리 시스템</title>
        <style>
            body {{ font-family: 'Noto Sans KR', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
            .stat-number {{ font-size: 2em; font-weight: bold; margin-bottom: 10px; }}
            .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
            .section {{ margin-bottom: 30px; }}
            .section h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .form-group {{ margin-bottom: 15px; }}
            .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #555; }}
            .form-group input, .form-group select, .form-group textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }}
            .btn {{ background: #3498db; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }}
            .btn:hover {{ background: #2980b9; }}
            .btn-success {{ background: #27ae60; }}
            .btn-success:hover {{ background: #229954; }}
            .btn-warning {{ background: #f39c12; }}
            .btn-warning:hover {{ background: #e67e22; }}
            .user-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .user-table th, .user-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            .user-table th {{ background: #f8f9fa; font-weight: bold; }}
            .status-active {{ color: #27ae60; font-weight: bold; }}
            .status-expired {{ color: #e74c3c; font-weight: bold; }}
            .actions {{ margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap; }}
            .result {{ margin-top: 20px; padding: 15px; border-radius: 5px; }}
            .result.success {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
            .result.error {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 GA4 권한 관리 시스템</h1>
            
            <!-- 통계 카드 -->
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len([u for u in TEST_USERS if u['status'] == 'active'])}</div>
                    <div class="stat-label">활성 사용자</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(PROPERTY_DATA)}</div>
                    <div class="stat-label">관리 중인 프로퍼티</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len([u for u in TEST_USERS if u['권한'] == 'analyst'])}</div>
                    <div class="stat-label">Analyst 권한</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len([u for u in TEST_USERS if u['권한'] == 'viewer'])}</div>
                    <div class="stat-label">Viewer 권한</div>
                </div>
            </div>

            <!-- 사용자 등록 폼 -->
            <div class="section">
                <h2>👤 사용자 등록</h2>
                <form id="registerForm" onsubmit="registerUser(event)">
                    <div class="form-group">
                        <label for="신청자">신청자:</label>
                        <input type="text" id="신청자" name="신청자" required>
                    </div>
                    <div class="form-group">
                        <label for="등록_계정_목록">등록할 계정 (여러 개는 쉼표로 구분):</label>
                        <textarea id="등록_계정_목록" name="등록_계정_목록" rows="3" placeholder="예: user1@example.com, user2@example.com" required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="property_ids">프로퍼티 ID:</label>
                        <select id="property_ids" name="property_ids" required>
                            <option value="">프로퍼티 선택</option>
                            <option value="462884506">462884506 - 아모레퍼시픽 웹사이트</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="권한">권한 레벨:</label>
                        <select id="권한" name="권한" required>
                            <option value="">권한 선택</option>
                            <option value="viewer">Viewer (읽기 전용)</option>
                            <option value="analyst">Analyst (분석 가능)</option>
                            <option value="editor">Editor (편집 가능, 7일 후 자동 다운그레이드)</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">사용자 등록</button>
                </form>
                <div id="registerResult"></div>
            </div>

            <!-- 현재 등록된 사용자 목록 -->
            <div class="section">
                <h2>📋 등록된 사용자 목록</h2>
                <table class="user-table" id="userTable">
                    <thead>
                        <tr>
                            <th>신청자</th>
                            <th>등록 계정</th>
                            <th>권한</th>
                            <th>상태</th>
                            <th>신청일</th>
                            <th>종료일</th>
                            <th>작업</th>
                        </tr>
                    </thead>
                    <tbody id="userTableBody">
                        <!-- 동적 로드 -->
                    </tbody>
                </table>
            </div>

            <!-- 관리 작업 -->
            <div class="section">
                <h2>⚙️ 시스템 관리</h2>
                <div class="actions">
                    <button class="btn btn-success" onclick="processQueue()">대기열 처리</button>
                    <button class="btn btn-warning" onclick="sendTestNotification()">테스트 알림 발송</button>
                    <button class="btn" onclick="getStats()">시스템 통계</button>
                    <button class="btn" onclick="loadUsers()">사용자 목록 새로고침</button>
                </div>
                <div id="systemResult"></div>
            </div>
        </div>

        <script>
            // 페이지 로드 시 사용자 목록 로드
            document.addEventListener('DOMContentLoaded', loadUsers);

            async function registerUser(event) {{
                event.preventDefault();
                const formData = new FormData(event.target);
                const result = document.getElementById('registerResult');
                
                try {{
                    const response = await fetch('/api/register', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const data = await response.json();
                    
                    if (data.status === 'success' || data.status === 'existing_extended' || data.status === 'existing_updated') {{
                        result.innerHTML = `<div class="result success">✅ ${{data.message}}</div>`;
                        event.target.reset();
                        loadUsers(); // 사용자 목록 새로고침
                    }} else {{
                        result.innerHTML = `<div class="result error">❌ ${{data.message || '등록 실패'}}</div>`;
                    }}
                }} catch (error) {{
                    result.innerHTML = `<div class="result error">❌ 오류: ${{error.message}}</div>`;
                }}
            }}

            async function loadUsers() {{
                const tbody = document.getElementById('userTableBody');
                
                try {{
                    const response = await fetch('/api/users');
                    const data = await response.json();
                    
                    tbody.innerHTML = data.users.map(user => `
                        <tr>
                            <td>${{user.신청자}}</td>
                            <td>${{user.등록_계정}}</td>
                            <td>${{user.권한}}</td>
                            <td class="status-${{user.status}}">${{user.status === 'active' ? '활성' : '만료'}}</td>
                            <td>${{user.신청일}}</td>
                            <td>${{user.종료일}}</td>
                            <td>
                                <button class="btn" style="font-size: 12px; padding: 5px 10px;" onclick="extendUser(${{user.id}})">연장</button>
                            </td>
                        </tr>
                    `).join('');
                }} catch (error) {{
                    tbody.innerHTML = '<tr><td colspan="7">사용자 목록 로드 실패</td></tr>';
                }}
            }}

            async function processQueue() {{
                const result = document.getElementById('systemResult');
                result.innerHTML = '<div class="result">🔄 대기열 처리 중...</div>';
                
                try {{
                    const response = await fetch('/api/process-queue', {{ method: 'POST' }});
                    const data = await response.json();
                    
                    result.innerHTML = `<div class="result success">✅ ${{data.message}}</div>`;
                }} catch (error) {{
                    result.innerHTML = `<div class="result error">❌ 대기열 처리 실패: ${{error.message}}</div>`;
                }}
            }}

            async function sendTestNotification() {{
                const email = prompt('테스트 알림을 받을 이메일을 입력하세요:');
                if (!email) return;
                
                const result = document.getElementById('systemResult');
                result.innerHTML = '<div class="result">📧 테스트 알림 발송 중...</div>';
                
                try {{
                    const response = await fetch('/api/send-test-notification', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ email, type: 'welcome' }})
                    }});
                    
                    const data = await response.json();
                    result.innerHTML = `<div class="result success">✅ ${{data.message}}</div>`;
                }} catch (error) {{
                    result.innerHTML = `<div class="result error">❌ 알림 발송 실패: ${{error.message}}</div>`;
                }}
            }}

            async function getStats() {{
                const result = document.getElementById('systemResult');
                result.innerHTML = '<div class="result">📊 통계 조회 중...</div>';
                
                try {{
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    
                    const stats = data.data.stats;
                    result.innerHTML = `
                        <div class="result success">
                            <h4>📊 시스템 통계</h4>
                            <p><strong>전체 사용자:</strong> ${{stats.total_users}}명</p>
                            <p><strong>활성 사용자:</strong> ${{stats.active_users}}명</p>
                            <p><strong>만료된 사용자:</strong> ${{stats.expired_users}}명</p>
                            <p><strong>관리 중인 프로퍼티:</strong> ${{stats.total_properties}}개</p>
                        </div>
                    `;
                }} catch (error) {{
                    result.innerHTML = `<div class="result error">❌ 통계 조회 실패: ${{error.message}}</div>`;
                }}
            }}

            async function extendUser(userId) {{
                if (!confirm('이 사용자의 권한을 30일 연장하시겠습니까?')) return;
                
                try {{
                    const response = await fetch(`/api/users/${{userId}}/extend`, {{ method: 'POST' }});
                    const data = await response.json();
                    
                    if (data.success) {{
                        alert('✅ 권한이 연장되었습니다.');
                        loadUsers();
                    }} else {{
                        alert('❌ 권한 연장 실패: ' + data.message);
                    }}
                }} catch (error) {{
                    alert('❌ 오류: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/api/users")
async def get_users():
    """사용자 목록 조회"""
    return {"success": True, "users": TEST_USERS}

@app.post("/api/register")
async def register_users(
    신청자: str = Form(...),
    등록_계정_목록: str = Form(...),
    property_ids: str = Form(...),
    권한: str = Form(...)
):
    """사용자 등록 API (중복 방지 로직 포함)"""
    try:
        # 이메일 목록 파싱
        emails = [email.strip() for email in 등록_계정_목록.split(',') if email.strip()]
        
        results = []
        new_registrations = 0
        existing_processed = 0
        
        for email in emails:
            # 기존 등록 체크
            existing_user = next((u for u in TEST_USERS if u['등록_계정'] == email and u['property_id'] == property_ids), None)
            
            if existing_user:
                if existing_user['권한'] == 권한:
                    # 같은 권한 - 만료일 연장
                    existing_user['종료일'] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    results.append({
                        "email": email,
                        "action": "extended",
                        "message": f"기존 등록 발견 - 만료일 연장됨 (권한: {권한})"
                    })
                    existing_processed += 1
                else:
                    # 다른 권한 - 권한 업데이트
                    old_permission = existing_user['권한']
                    existing_user['권한'] = 권한
                    existing_user['종료일'] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    results.append({
                        "email": email,
                        "action": "updated",
                        "message": f"기존 등록 권한 업데이트: {old_permission} → {권한}"
                    })
                    existing_processed += 1
            else:
                # 신규 등록
                new_user = {
                    "id": max([u['id'] for u in TEST_USERS], default=0) + 1,
                    "신청자": 신청자,
                    "등록_계정": email,
                    "property_id": property_ids,
                    "권한": 권한,
                    "status": "active",
                    "신청일": datetime.now().strftime('%Y-%m-%d'),
                    "종료일": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                }
                TEST_USERS.append(new_user)
                results.append({
                    "email": email,
                    "action": "registered",
                    "message": f"신규 등록 완료 (권한: {권한})"
                })
                new_registrations += 1
        
        # 응답 메시지 생성
        if len(emails) == 1:
            # 단일 사용자
            action_info = results[0]
            if action_info['action'] == 'extended':
                return {"status": "existing_extended", "message": action_info['message']}
            elif action_info['action'] == 'updated':
                return {"status": "existing_updated", "message": action_info['message']}
            else:
                return {"status": "success", "message": action_info['message']}
        else:
            # 다중 사용자
            return {
                "status": "success",
                "message": f"처리 완료 - 신규등록: {new_registrations}건, 기존처리: {existing_processed}건",
                "results": results
            }
        
    except Exception as e:
        return {"status": "error", "message": f"등록 처리 중 오류: {str(e)}"}

@app.post("/api/process-queue")
async def process_queue():
    """대기열 처리"""
    return {"success": True, "message": "대기열 처리가 완료되었습니다."}

@app.post("/api/send-test-notification")
async def send_test_notification(request: Request):
    """테스트 알림 발송"""
    data = await request.json()
    email = data.get("email")
    return {"success": True, "message": f"테스트 알림이 {email}로 발송되었습니다."}

@app.get("/api/stats")
async def get_stats():
    """시스템 통계"""
    active_users = len([u for u in TEST_USERS if u['status'] == 'active'])
    expired_users = len([u for u in TEST_USERS if u['status'] == 'expired'])
    
    return {
        "success": True,
        "data": {
            "stats": {
                "total_users": len(TEST_USERS),
                "active_users": active_users,
                "expired_users": expired_users,
                "total_properties": len(PROPERTY_DATA)
            }
        }
    }

@app.post("/api/users/{user_id}/extend")
async def extend_user(user_id: int):
    """사용자 권한 연장"""
    user = next((u for u in TEST_USERS if u['id'] == user_id), None)
    
    if user:
        user['종료일'] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        return {"success": True, "message": "권한이 30일 연장되었습니다."}
    else:
        return {"success": False, "message": "사용자를 찾을 수 없습니다."}

if __name__ == "__main__":
    print("🚀 GA4 권한 관리 시스템 테스트 서버 시작")
    print("📍 접속 주소: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000) 