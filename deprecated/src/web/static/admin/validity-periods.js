/**
 * 유효기간 관리 모듈
 * ==================
 * 
 * 단일 책임 원칙(SRP)에 따라 유효기간 관련 기능만 처리
 */

class ValidityPeriodsManager {
    constructor() {
        this.currentPeriodId = null;
    }

    // 초기화
    async initialize() {
        await this.loadValidityPeriods();
    }

    // 유효기간 목록 로드
    async loadValidityPeriods() {
        try {
            const response = await fetch('/api/admin/validity-periods');
            const data = await response.json();
            
            if (data.success) {
                this.displayValidityPeriods(data.periods);
            } else {
                AdminUtils.showAlert('유효기간 설정을 불러오는데 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('유효기간 로드 실패:', error);
            AdminUtils.showAlert('유효기간 설정을 불러오는데 실패했습니다.', 'danger');
        }
    }

    // 유효기간 목록 표시
    displayValidityPeriods(periods) {
        const tbody = document.getElementById('periods-table');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        periods.forEach(period => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <span class="badge bg-${this.getRoleBadgeColor(period.role)}">${this.getRoleDisplayName(period.role)}</span>
                </td>
                <td>${period.period_days}일</td>
                <td>${period.description || '-'}</td>
                <td>
                    ${period.is_active ? 
                        '<span class="badge bg-success">활성</span>' : 
                        '<span class="badge bg-secondary">비활성</span>'
                    }
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-2" onclick="validityPeriodsManager.editPeriod(${period.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="validityPeriodsManager.deletePeriod(${period.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // 역할 뱃지 색상
    getRoleBadgeColor(role) {
        const colors = {
            'viewer': 'info',
            'analyst': 'warning', 
            'editor': 'danger'
        };
        return colors[role] || 'secondary';
    }

    // 역할 표시명
    getRoleDisplayName(role) {
        const names = {
            'viewer': 'Viewer',
            'analyst': 'Analyst',
            'editor': 'Editor'
        };
        return names[role] || role;
    }

    // 새 유효기간 추가
    addNewPeriod() {
        this.currentPeriodId = null;
        document.getElementById('period-form').reset();
        document.getElementById('period-active').checked = true;
        const modal = new bootstrap.Modal(document.getElementById('periodModal'));
        modal.show();
    }

    // 유효기간 편집
    async editPeriod(id) {
        try {
            const response = await fetch(`/api/admin/validity-periods/${id}`);
            const data = await response.json();
            
            if (data.success && data.period) {
                const period = data.period;
                this.currentPeriodId = id;
                
                // 안전한 접근 패턴 적용
                document.getElementById('period-id').value = id;
                document.getElementById('period-role').value = period.role || '';
                document.getElementById('period-days').value = period.period_days || '';
                document.getElementById('period-description').value = period.description || '';
                document.getElementById('period-active').checked = period.is_active || false;
                
                const modal = new bootstrap.Modal(document.getElementById('periodModal'));
                modal.show();
            } else {
                AdminUtils.showAlert('유효기간 정보를 불러오는데 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('유효기간 로드 실패:', error);
            AdminUtils.showAlert('유효기간 정보를 불러오는데 실패했습니다.', 'danger');
        }
    }

    // 유효기간 저장
    async savePeriod() {
        // 입력값 검증 및 안전한 변환
        const daysValue = document.getElementById('period-days').value;
        const periodDays = parseInt(daysValue);
        
        // 유효성 검사
        if (!daysValue || isNaN(periodDays) || periodDays <= 0) {
            AdminUtils.showAlert('유효한 일수를 입력해주세요. (1일 이상)', 'warning');
            return;
        }
        
        const formData = {
            role: document.getElementById('period-role').value,
            period_days: periodDays,
            description: document.getElementById('period-description').value,
            is_active: document.getElementById('period-active').checked
        };
        
        try {
            const url = this.currentPeriodId ? 
                `/api/admin/validity-periods/${this.currentPeriodId}` : 
                '/api/admin/validity-periods';
            const method = this.currentPeriodId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                AdminUtils.showAlert('유효기간 설정이 저장되었습니다.', 'success');
                await this.loadValidityPeriods();
                bootstrap.Modal.getInstance(document.getElementById('periodModal')).hide();
            } else {
                AdminUtils.showAlert(data.message || '저장에 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('저장 실패:', error);
            AdminUtils.showAlert('저장 중 오류가 발생했습니다.', 'danger');
        }
    }

    // 유효기간 삭제
    async deletePeriod(id) {
        if (!confirm('이 유효기간 설정을 삭제하시겠습니까?')) return;
        
        try {
            const response = await fetch(`/api/admin/validity-periods/${id}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                AdminUtils.showAlert('유효기간 설정이 삭제되었습니다.', 'success');
                await this.loadValidityPeriods();
            } else {
                AdminUtils.showAlert(data.message || '삭제에 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('삭제 실패:', error);
            AdminUtils.showAlert('삭제 중 오류가 발생했습니다.', 'danger');
        }
    }
}

// 전역 인스턴스 생성
const validityPeriodsManager = new ValidityPeriodsManager(); 