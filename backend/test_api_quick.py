#!/usr/bin/env python3
"""
Quick API test script for GA4 Admin Automation System
Tests basic functionality: user registration, login, and authentication
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"


async def test_api():
    """Test basic API functionality"""
    print(f"🚀 Testing GA4 Admin Automation API at {BASE_URL}")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Health Check
        print("1️⃣ Testing health endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✅ Health check passed: {health_data['status']}")
                print(f"   📊 Service: {health_data['service']} v{health_data['version']}")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
            
        # Test 2: User Registration
        print("\n2️⃣ Testing user registration...")
        test_user = {
            "email": f"test_{int(datetime.now().timestamp())}@example.com",
            "name": "Test User",
            "company": "Test Company",
            "password": "testpassword123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/auth/register", json=test_user)
            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✅ User registration successful: {user_data['email']}")
                test_email = user_data['email']
            else:
                print(f"   ❌ User registration failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                # Continue with existing user for login test
                test_email = test_user['email']
        except Exception as e:
            print(f"   ❌ User registration error: {e}")
            test_email = test_user['email']
            
        # Test 3: User Login
        print("\n3️⃣ Testing user login...")
        login_data = {
            "email": test_email,
            "password": "testpassword123"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/auth/login", json=login_data)
            if response.status_code == 200:
                auth_response = response.json()
                print(f"   ✅ Login successful!")
                print(f"   🔑 Token type: {auth_response.get('token_type', 'N/A')}")
                access_token = auth_response.get('access_token')
                if access_token:
                    print(f"   🎫 Access token received (length: {len(access_token)})")
                else:
                    print(f"   ⚠️ No access token in response")
            else:
                print(f"   ❌ Login failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                access_token = None
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            access_token = None
            
        # Test 4: Authenticated Request (if we have a token)
        if access_token:
            print("\n4️⃣ Testing authenticated request...")
            headers = {"Authorization": f"Bearer {access_token}"}
            
            try:
                response = await client.get(f"{BASE_URL}/api/users/me", headers=headers)
                if response.status_code == 200:
                    user_info = response.json()
                    print(f"   ✅ Authenticated request successful!")
                    print(f"   👤 User: {user_info.get('email', 'N/A')}")
                    print(f"   🎭 Role: {user_info.get('role', 'N/A')}")
                else:
                    print(f"   ❌ Authenticated request failed: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Authenticated request error: {e}")
        else:
            print("\n4️⃣ Skipping authenticated request test (no token)")
            
        # Test 5: API Documentation
        print("\n5️⃣ Testing API documentation...")
        try:
            response = await client.get(f"{BASE_URL}/api/openapi.json")
            if response.status_code == 200:
                openapi_spec = response.json()
                print(f"   ✅ OpenAPI spec accessible")
                print(f"   📚 API Title: {openapi_spec.get('info', {}).get('title', 'N/A')}")
                print(f"   🔢 API Version: {openapi_spec.get('info', {}).get('version', 'N/A')}")
                endpoints_count = len(openapi_spec.get('paths', {}))
                print(f"   🛣️ Total endpoints: {endpoints_count}")
            else:
                print(f"   ❌ API documentation not accessible: {response.status_code}")
        except Exception as e:
            print(f"   ❌ API documentation error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 API testing completed!")
    return True


if __name__ == "__main__":
    asyncio.run(test_api())