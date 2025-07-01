#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
중복 등록 방지 시스템 테스트 서버
================================

Playwright 테스트용 간단한 서버입니다.
"""

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Any
import uvicorn

# 테스트용 메모리 데이터베이스
fake_users_db = [
    {
        "email": "existing.user@example.com",
        "property_id": "462884506",
        "permission": "analyst",
        "status": "active",
        "created_at": "2025-06-28"
    }
]

app = FastAPI(title="GA4 중복 등록 방지 테스트 서버")

@app.get("/", response_class=HTMLResponse)
async def home():
    """메인 페이지"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GA4 중복 등록 방지 테스트</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { width: 100%; padding: 8px; margin-bottom: 10px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 GA4 중복 등록 방지 시스템 테스트</h1>
            
            <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3>📋 기존 등록된 테스트 사용자:</h3>
                <ul>
                    <li><strong>existing.user@example.com</strong> - Property: 462884506 - Permission: analyst</li>
                </ul>
                <p><em>이 사용자로 재등록을 시도하면 중복 체크가 작동합니다.</em></p>
            </div>
            
            <form id="registerForm">
                <div class="form-group">
                    <label for="applicant">신청자:</label>
                    <input type="text" id="applicant" name="applicant" value="테스트담당자" required>
                </div>
                
                <div class="form-group">
                    <label for="emails">등록할 이메일 (쉼표로 구분):</label>
                    <input type="text" id="emails" name="emails" 
                           placeholder="new.user@example.com, existing.user@example.com" required>
                </div>
                
                <div class="form-group">
                    <label for="property">프로퍼티 ID:</label>
                    <select id="property" name="property" required>
                        <option value="462884506">462884506 - Test Property</option>
                        <option value="123456789">123456789 - Other Property</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="permission">권한:</label>
                    <select id="permission" name="permission" required>
                        <option value="analyst">Analyst</option>
                        <option value="editor">Editor</option>
                        <option value="viewer">Viewer</option>
                    </select>
                </div>
                
                <button type="submit" id="submitBtn">🚀 등록하기</button>
            </form>
            
            <div id="result" style="display: none;"></div>
        </div>
        
        <script>
            document.getElementById('registerForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const submitBtn = document.getElementById('submitBtn');
                const resultDiv = document.getElementById('result');
                
                submitBtn.disabled = true;
                submitBtn.textContent = '처리 중...';
                
                const formData = new FormData();
                formData.append('신청자', document.getElementById('applicant').value);
                formData.append('등록_계정_목록', document.getElementById('emails').value);
                formData.append('property_ids', document.getElementById('property').value);
                formData.append('권한', document.getElementById('permission').value);
                
                try {
                    const response = await fetch('/api/register', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    resultDiv.style.display = 'block';
                    if (response.ok) {
                        resultDiv.className = 'result success';
                        resultDiv.innerHTML = `
                            <h3>✅ ${result.message}</h3>
                            <div style="margin-top: 10px;">
                                ${result.data.results.map(r => 
                                    `<p><strong>${r.email}</strong>: ${r.status} ${r.message ? '- ' + r.message : ''}</p>`
                                ).join('')}
                            </div>
                        `;
                    } else {
                        resultDiv.className = 'result error';
                        resultDiv.innerHTML = `<h3>❌ 오류: ${result.detail}</h3>`;
                    }
                } catch (error) {
                    resultDiv.style.display = 'block';
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `<h3>❌ 네트워크 오류: ${error.message}</h3>`;
                }
                
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 등록하기';
            });
        </script>
    </body>
    </html>
    """

@app.post("/api/register")
async def register_users(
    신청자: str = Form(...),
    등록_계정_목록: str = Form(...),
    property_ids: str = Form(...),
    권한: str = Form(...)
):
    """중복 등록 방지 로직이 적용된 사용자 등록 API"""
    try:
        # 이메일 목록 파싱
        emails = [email.strip() for email in 등록_계정_목록.split(',')]
        
        results = []
        
        for email in emails:
            # 기존 등록 체크
            existing_user = None
            for user in fake_users_db:
                if user['email'] == email and user['property_id'] == property_ids:
                    existing_user = user
                    break
            
            if existing_user:
                # 중복 등록 처리
                if existing_user['permission'] == 권한:
                    # 같은 권한으로 이미 등록됨 - 만료일 연장
                    results.append({
                        "email": email,
                        "property_id": property_ids,
                        "status": "existing_extended",
                        "message": f"기존 등록 발견 - 만료일 연장됨 (권한: {권한})"
                    })
                else:
                    # 다른 권한으로 등록됨 - 권한 업데이트
                    existing_user['permission'] = 권한
                    results.append({
                        "email": email,
                        "property_id": property_ids,
                        "status": "existing_updated",
                        "message": f"기존 등록 권한 업데이트: {existing_user['permission']} → {권한}"
                    })
            else:
                # 신규 등록
                fake_users_db.append({
                    "email": email,
                    "property_id": property_ids,
                    "permission": 권한,
                    "status": "active",
                    "created_at": "2025-06-28"
                })
                
                results.append({
                    "email": email,
                    "property_id": property_ids,
                    "status": "success",
                    "message": f"신규 등록 완료 (권한: {권한})"
                })
        
        # 통계
        success_count = len([r for r in results if r['status'] == 'success'])
        existing_count = len([r for r in results if 'existing' in r['status']])
        
        return JSONResponse({
            "success": True,
            "message": f"처리 완료 - 신규등록: {success_count}건, 기존처리: {existing_count}건",
            "data": {"results": results}
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users")
async def get_users():
    """등록된 사용자 목록 조회"""
    return {"users": fake_users_db}

if __name__ == "__main__":
    print("🚀 중복 등록 방지 테스트 서버 시작")
    print("📍 접속 주소: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 