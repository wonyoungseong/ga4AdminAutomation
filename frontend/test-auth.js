#!/usr/bin/env node

/**
 * Authentication Flow Test Script
 * Tests the complete authentication flow including login, token refresh, and API calls
 */

const API_BASE_URL = 'http://localhost:8000';

async function makeRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });
        
        const data = await response.json();
        return { response, data };
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}

async function testAuthFlow() {
    console.log('🔍 Testing Authentication Flow...\n');
    
    // Step 1: Login
    console.log('1. Testing Login...');
    const { response: loginResponse, data: loginData } = await makeRequest(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        body: JSON.stringify({
            email: 'admin@test.com',
            password: 'admin123'
        }),
    });
    
    if (loginResponse.ok) {
        console.log('✅ Login successful');
        console.log(`   Access Token: ${loginData.access_token.substring(0, 20)}...`);
        console.log(`   Refresh Token: ${loginData.refresh_token.substring(0, 20)}...`);
        console.log(`   User: ${loginData.user.name} (${loginData.user.email})`);
    } else {
        console.error('❌ Login failed:', loginData);
        return;
    }
    
    // Step 2: Test API call with access token
    console.log('\n2. Testing API call with access token...');
    const { response: meResponse, data: meData } = await makeRequest(`${API_BASE_URL}/api/auth/me`, {
        headers: {
            'Authorization': `Bearer ${loginData.access_token}`
        }
    });
    
    if (meResponse.ok) {
        console.log('✅ API call successful');
        console.log(`   Current user: ${meData.name} (${meData.email})`);
    } else {
        console.error('❌ API call failed:', meData);
    }
    
    // Step 3: Test token refresh
    console.log('\n3. Testing token refresh...');
    const { response: refreshResponse, data: refreshData } = await makeRequest(
        `${API_BASE_URL}/api/auth/refresh?refresh_token=${encodeURIComponent(loginData.refresh_token)}`, 
        {
            method: 'POST'
        }
    );
    
    if (refreshResponse.ok) {
        console.log('✅ Token refresh successful');
        console.log(`   New Access Token: ${refreshData.access_token.substring(0, 20)}...`);
        console.log(`   New Refresh Token: ${refreshData.refresh_token.substring(0, 20)}...`);
    } else {
        console.error('❌ Token refresh failed:', refreshData);
        return;
    }
    
    // Step 4: Test API call with new access token
    console.log('\n4. Testing API call with refreshed token...');
    const { response: me2Response, data: me2Data } = await makeRequest(`${API_BASE_URL}/api/auth/me`, {
        headers: {
            'Authorization': `Bearer ${refreshData.access_token}`
        }
    });
    
    if (me2Response.ok) {
        console.log('✅ API call with refreshed token successful');
        console.log(`   Current user: ${me2Data.name} (${me2Data.email})`);
    } else {
        console.error('❌ API call with refreshed token failed:', me2Data);
    }
    
    // Step 5: Test API call with expired/invalid token
    console.log('\n5. Testing API call with invalid token...');
    const { response: invalidResponse, data: invalidData } = await makeRequest(`${API_BASE_URL}/api/auth/me`, {
        headers: {
            'Authorization': `Bearer invalid_token_here`
        }
    });
    
    if (invalidResponse.status === 401) {
        console.log('✅ Invalid token correctly rejected');
        console.log(`   Error: ${invalidData.message || invalidData.detail}`);
    } else {
        console.error('❌ Invalid token should have been rejected');
    }
    
    console.log('\n🎉 Authentication flow test completed!');
}

testAuthFlow().catch(console.error);