/**
 * 담당자 관리 모듈
 * ================
 * 
 * 단일 책임 원칙(SRP)에 따라 담당자 관련 기능만 처리
 */

class ResponsiblePersonsManager {
    constructor() {
        this.currentManagerId = null;
    }

    // 초기화
    async initialize() {
        await this.loadResponsiblePersons();
    }

    // 담당자 목록 로드
    async loadResponsiblePersons() {
        try {
            const response = await fetch('/api/admin/responsible-persons');
            const data = await response.json();
            
            if (data.success) {
                this.displayResponsiblePersons(data.persons);
            } else {
                AdminUtils.showAlert('담당자 정보를 불러오는데 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('담당자 로드 실패:', error);
            AdminUtils.showAlert('담당자 정보를 불러오는데 실패했습니다.', 'danger');
        }
    }

    // 담당자 목록 표시
    displayResponsiblePersons(persons) {
        const tbody = document.getElementById('managers-table');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        persons.forEach(person => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${person.name || '-'}</td>
                <td>${person.email || '-'}</td>
                <td>${person.account_name || '전체'}</td>
                <td>${person.property_name || '전체'}</td>
                <td>
                    <span class="badge bg-primary">${person.role || '-'}</span>
                </td>
                <td>
                    ${person.notification_enabled ? 
                        '<span class="badge bg-success">활성</span>' : 
                        '<span class="badge bg-secondary">비활성</span>'
                    }
                </td>
                <td>
                    ${person.is_active ? 
                        '<span class="badge bg-success">활성</span>' : 
                        '<span class="badge bg-secondary">비활성</span>'
                    }
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-2" onclick="responsiblePersonsManager.editManager(${person.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="responsiblePersonsManager.deleteManager(${person.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // 새 담당자 추가
    addNewManager() {
        this.currentManagerId = null;
        document.getElementById('manager-form').reset();
        document.getElementById('manager-notification').checked = true;
        document.getElementById('manager-active').checked = true;
        const modal = new bootstrap.Modal(document.getElementById('managerModal'));
        modal.show();
    }

    // 담당자 편집
    async editManager(id) {
        try {
            const response = await fetch(`/api/admin/responsible-persons/${id}`);
            const data = await response.json();
            
            if (data.success && data.person) {
                const person = data.person;
                this.currentManagerId = id;
                
                // 안전한 접근 패턴 적용
                document.getElementById('manager-id').value = id;
                document.getElementById('manager-name').value = person.name || '';
                document.getElementById('manager-email').value = person.email || '';
                document.getElementById('manager-account').value = person.account_id || '';
                document.getElementById('manager-property').value = person.property_id || '';
                document.getElementById('manager-role').value = person.role || 'manager';
                document.getElementById('manager-notification').checked = person.notification_enabled || false;
                document.getElementById('manager-active').checked = person.is_active || false;
                
                const modal = new bootstrap.Modal(document.getElementById('managerModal'));
                modal.show();
            } else {
                AdminUtils.showAlert('담당자 정보를 불러오는데 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('담당자 로드 실패:', error);
            AdminUtils.showAlert('담당자 정보를 불러오는데 실패했습니다.', 'danger');
        }
    }

    // 담당자 저장
    async saveManager() {
        const formData = {
            name: document.getElementById('manager-name').value,
            email: document.getElementById('manager-email').value,
            account_id: document.getElementById('manager-account').value || null,
            property_id: document.getElementById('manager-property').value || null,
            role: document.getElementById('manager-role').value,
            notification_enabled: document.getElementById('manager-notification').checked,
            is_active: document.getElementById('manager-active').checked
        };
        
        try {
            const url = this.currentManagerId ? 
                `/api/admin/responsible-persons/${this.currentManagerId}` : 
                '/api/admin/responsible-persons';
            const method = this.currentManagerId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                AdminUtils.showAlert('담당자 정보가 저장되었습니다.', 'success');
                await this.loadResponsiblePersons();
                bootstrap.Modal.getInstance(document.getElementById('managerModal')).hide();
            } else {
                AdminUtils.showAlert(data.message || '저장에 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('저장 실패:', error);
            AdminUtils.showAlert('저장 중 오류가 발생했습니다.', 'danger');
        }
    }

    // 담당자 삭제
    async deleteManager(id) {
        if (!confirm('이 담당자를 삭제하시겠습니까?')) return;
        
        try {
            const response = await fetch(`/api/admin/responsible-persons/${id}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                AdminUtils.showAlert('담당자가 삭제되었습니다.', 'success');
                await this.loadResponsiblePersons();
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
const responsiblePersonsManager = new ResponsiblePersonsManager(); 