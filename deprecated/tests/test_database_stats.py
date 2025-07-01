#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 통계 기능 테스트
============================

TDD 방식으로 대시보드에 필요한 통계 데이터 구조를 테스트
"""

import pytest
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestDatabaseStats:
    """데이터베이스 통계 테스트"""
    
    def test_expected_stats_structure(self):
        """대시보드에서 기대하는 통계 데이터 구조 테스트"""
        # 대시보드 템플릿에서 사용하는 키들
        expected_keys = [
            'total_accounts',
            'total_properties', 
            'active_users',
            'expiring_soon'
        ]
        
        # 테스트용 통계 데이터
        test_stats = {
            'total_accounts': 5,
            'total_properties': 12,
            'active_users': 25,
            'expiring_soon': 3
        }
        
        # 모든 필요한 키가 존재하는지 확인
        for key in expected_keys:
            assert key in test_stats, f"필수 키 {key}가 없습니다"
            assert isinstance(test_stats[key], int), f"{key}는 정수여야 합니다"
    
    def test_database_table_mapping(self):
        """데이터베이스 테이블과 통계 키 매핑 테스트"""
        # 현재 get_database_stats가 반환하는 형식
        current_stats = {
            'ga4_accounts': 5,
            'ga4_properties': 12,
            'user_registrations': 25,
            'notification_logs': 100,
            'audit_logs': 50
        }
        
        # 대시보드에 필요한 형식으로 변환
        dashboard_stats = {
            'total_accounts': current_stats.get('ga4_accounts', 0),
            'total_properties': current_stats.get('ga4_properties', 0),
            'active_users': current_stats.get('user_registrations', 0),
            'total_notifications': current_stats.get('notification_logs', 0),
            'total_audit_logs': current_stats.get('audit_logs', 0),
            'expiring_soon': 0  # 별도 쿼리 필요
        }
        
        assert dashboard_stats['total_accounts'] == 5
        assert dashboard_stats['total_properties'] == 12
        assert dashboard_stats['active_users'] == 25
        assert dashboard_stats['expiring_soon'] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 