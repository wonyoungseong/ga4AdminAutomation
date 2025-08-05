#!/usr/bin/env python3
"""
Master Test Runner - Execute All Authentication Tests
"""

import asyncio
import subprocess
import sys
import time
from datetime import datetime

async def run_test_script(script_name, description):
    """Run a test script and capture results"""
    print(f"\n{'='*80}")
    print(f"🧪 {description}")
    print(f"{'='*80}")
    
    try:
        # Run the script
        result = subprocess.run([
            sys.executable, script_name
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(result.stdout)
            return True, "SUCCESS"
        else:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False, f"FAILED (exit code: {result.returncode})"
            
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, f"ERROR: {str(e)}"

async def main():
    """Run all authentication tests"""
    print("🔐 GA4 Admin Authentication System - Master Test Suite")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 80)
    
    test_scripts = [
        ("test_auth_api.py", "Basic Authentication API Testing"),
        ("test_frontend_flow.py", "Frontend Authentication Flow Simulation"),
        ("test_rbac_and_refresh.py", "RBAC and Token Management Testing"),
    ]
    
    results = []
    total_time_start = time.time()
    
    for script, description in test_scripts:
        test_start = time.time()
        success, status = await run_test_script(script, description)
        test_duration = time.time() - test_start
        
        results.append({
            'script': script,
            'description': description,
            'success': success,
            'status': status,
            'duration': test_duration
        })
        
        print(f"\n⏱️  Test completed in {test_duration:.2f} seconds")
        
        # Brief pause between tests
        await asyncio.sleep(1)
    
    total_duration = time.time() - total_time_start
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {result['description']}")
        print(f"   Script: {result['script']}")
        print(f"   Status: {result['status']}")
        print(f"   Duration: {result['duration']:.2f}s")
        print()
    
    print(f"📈 Overall Results: {passed}/{total} test suites passed")
    print(f"⏱️  Total execution time: {total_duration:.2f} seconds")
    
    if passed == total:
        print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
        print("✅ The authentication system is working correctly")
        print("✅ Backend is ready to support frontend authentication")
        print("\n📋 Report available in: AUTHENTICATION_TEST_REPORT.md")
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        print("❌ Please review the detailed output above")
    
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)