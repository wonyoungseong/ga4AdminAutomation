// 관리자 설정 페이지 JavaScript

// 전역 변수
let currentPeriodId = null;
let currentManagerId = null;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    loadValidityPeriods();
    loadResponsiblePersons();
    loadNotificationSettings();
    loadSystemSettings();
    loadAccounts();
    loadProperties();
});

// 유효기간 설정 관련 함수들
async function loadValidityPeriods() {
    try {
        const response = await fetch('/api/admin/validity-periods');
        const data = await response.json();
        
        if (data.success) {
            displayValidityPeriods(data.periods);
        }
    } catch (error) {
        console.error('유효기간 로드 실패:', error);
        showAlert('유효기간 설정을 불러오는데 실패했습니다.', 'danger');
    }
}

function displayValidityPeriods(periods) {
    const tbody = document.getElementById('periods-table');
    tbody.innerHTML = '';
    
    periods.forEach(period => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <span class="badge bg-${getRoleBadgeColor(period.role)}">${getRoleDisplayName(period.role)}</span>
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
                <button class="btn btn-sm btn-outline-primary me-2" onclick="editPeriod(${period.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deletePeriod(${period.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function getRoleBadgeColor(role) {
    const colors = {
        'viewer': 'info',
        'analyst': 'warning', 
        'editor': 'danger'
    };
    return colors[role] || 'secondary';
}

function getRoleDisplayName(role) {
    const names = {
        'viewer': 'Viewer',
        'analyst': 'Analyst',
        'editor': 'Editor'
    };
    return names[role] || role;
}

function addNewPeriod() {
    currentPeriodId = null;
    document.getElementById('period-form').reset();
    document.getElementById('period-active').checked = true;
    const modal = new bootstrap.Modal(document.getElementById('periodModal'));
    modal.show();
}

function editPeriod(id) {
    // 기존 데이터 로드하여 모달에 표시
    fetch(`/api/admin/validity-periods/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const period = data.period;
                currentPeriodId = id;
                document.getElementById('period-id').value = id;
                document.getElementById('period-role').value = period.role;
                document.getElementById('period-days').value = period.period_days;
                document.getElementById('period-description').value = period.description || '';
                document.getElementById('period-active').checked = period.is_active;
                
                const modal = new bootstrap.Modal(document.getElementById('periodModal'));
                modal.show();
            }
        })
        .catch(error => {
            console.error('유효기간 로드 실패:', error);
            showAlert('유효기간 정보를 불러오는데 실패했습니다.', 'danger');
        });
}

async function savePeriod() {
    const formData = {
        role: document.getElementById('period-role').value,
        period_days: parseInt(document.getElementById('period-days').value),
        description: document.getElementById('period-description').value,
        is_active: document.getElementById('period-active').checked
    };
    
    try {
        const url = currentPeriodId ? 
            `/api/admin/validity-periods/${currentPeriodId}` : 
            '/api/admin/validity-periods';
        const method = currentPeriodId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('유효기간 설정이 저장되었습니다.', 'success');
            loadValidityPeriods();
            bootstrap.Modal.getInstance(document.getElementById('periodModal')).hide();
        } else {
            showAlert(data.message || '저장에 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('저장 실패:', error);
        showAlert('저장 중 오류가 발생했습니다.', 'danger');
    }
}

async function deletePeriod(id) {
    if (!confirm('이 유효기간 설정을 삭제하시겠습니까?')) return;
    
    try {
        const response = await fetch(`/api/admin/validity-periods/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('유효기간 설정이 삭제되었습니다.', 'success');
            loadValidityPeriods();
        } else {
            showAlert(data.message || '삭제에 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('삭제 실패:', error);
        showAlert('삭제 중 오류가 발생했습니다.', 'danger');
    }
}

// 담당자 관리 관련 함수들
async function loadResponsiblePersons() {
    try {
        const response = await fetch('/api/admin/responsible-persons');
        const data = await response.json();
        
        if (data.success) {
            displayResponsiblePersons(data.persons);
        }
    } catch (error) {
        console.error('담당자 로드 실패:', error);
        showAlert('담당자 정보를 불러오는데 실패했습니다.', 'danger');
    }
}

function displayResponsiblePersons(persons) {
    const tbody = document.getElementById('managers-table');
    tbody.innerHTML = '';
    
    persons.forEach(person => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${person.name}</td>
            <td>${person.email}</td>
            <td>${person.account_name || '전체'}</td>
            <td>${person.property_name || '전체'}</td>
            <td>
                <span class="badge bg-primary">${person.role}</span>
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
                <button class="btn btn-sm btn-outline-primary me-2" onclick="editManager(${person.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteManager(${person.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function addNewManager() {
    currentManagerId = null;
    document.getElementById('manager-form').reset();
    document.getElementById('manager-notification').checked = true;
    document.getElementById('manager-active').checked = true;
    const modal = new bootstrap.Modal(document.getElementById('managerModal'));
    modal.show();
}

function editManager(id) {
    fetch(`/api/admin/responsible-persons/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const person = data.person;
                currentManagerId = id;
                document.getElementById('manager-id').value = id;
                document.getElementById('manager-name').value = person.name;
                document.getElementById('manager-email').value = person.email;
                document.getElementById('manager-account').value = person.account_id || '';
                document.getElementById('manager-property').value = person.property_id || '';
                document.getElementById('manager-role').value = person.role;
                document.getElementById('manager-notification').checked = person.notification_enabled;
                document.getElementById('manager-active').checked = person.is_active;
                
                const modal = new bootstrap.Modal(document.getElementById('managerModal'));
                modal.show();
            }
        })
        .catch(error => {
            console.error('담당자 로드 실패:', error);
            showAlert('담당자 정보를 불러오는데 실패했습니다.', 'danger');
        });
}

async function saveManager() {
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
        const url = currentManagerId ? 
            `/api/admin/responsible-persons/${currentManagerId}` : 
            '/api/admin/responsible-persons';
        const method = currentManagerId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('담당자 정보가 저장되었습니다.', 'success');
            loadResponsiblePersons();
            bootstrap.Modal.getInstance(document.getElementById('managerModal')).hide();
        } else {
            showAlert(data.message || '저장에 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('저장 실패:', error);
        showAlert('저장 중 오류가 발생했습니다.', 'danger');
    }
}

async function deleteManager(id) {
    if (!confirm('이 담당자를 삭제하시겠습니까?')) return;
    
    try {
        const response = await fetch(`/api/admin/responsible-persons/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('담당자가 삭제되었습니다.', 'success');
            loadResponsiblePersons();
        } else {
            showAlert(data.message || '삭제에 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('삭제 실패:', error);
        showAlert('삭제 중 오류가 발생했습니다.', 'danger');
    }
}

// 알림 설정 관련 함수들
async function loadNotificationSettings() {
    try {
        const response = await fetch('/api/admin/notification-settings');
        const data = await response.json();
        
        if (data.success) {
            displayNotificationSettings(data.settings);
        }
    } catch (error) {
        console.error('알림 설정 로드 실패:', error);
        showAlert('알림 설정을 불러오는데 실패했습니다.', 'danger');
    }
}

function displayNotificationSettings(settings) {
    const tbody = document.getElementById('notifications-table');
    tbody.innerHTML = '';
    
    settings.forEach(setting => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${getNotificationTypeDisplayName(setting.notification_type)}</td>
            <td>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" 
                           ${setting.enabled ? 'checked' : ''} 
                           onchange="toggleNotification('${setting.notification_type}', this.checked)">
                </div>
            </td>
            <td>${setting.trigger_days}</td>
            <td>${setting.template_subject}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="editNotification('${setting.notification_type}')">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function getNotificationTypeDisplayName(type) {
    const names = {
        'immediate_approval': '즉시 승인 알림',
        'daily_summary': '일일 요약 보고서',
        'expiry_warning': '만료 경고 알림',
        'expiry_notice': '만료 안내 알림'
    };
    return names[type] || type;
}

async function toggleNotification(type, enabled) {
    try {
        const response = await fetch(`/api/admin/notification-settings/${type}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({enabled: enabled})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`알림 설정이 ${enabled ? '활성화' : '비활성화'}되었습니다.`, 'success');
        } else {
            showAlert(data.message || '설정 변경에 실패했습니다.', 'danger');
            // 실패 시 체크박스 원상복구
            event.target.checked = !enabled;
        }
    } catch (error) {
        console.error('알림 설정 변경 실패:', error);
        showAlert('설정 변경 중 오류가 발생했습니다.', 'danger');
        event.target.checked = !enabled;
    }
}

// 시스템 설정 관련 함수들
async function loadSystemSettings() {
    try {
        const response = await fetch('/api/admin/system-settings');
        const data = await response.json();
        
        if (data.success) {
            const settings = data.settings;
            
            // 자동 승인 설정
            document.getElementById('auto-approval-viewer').checked = 
                settings.auto_approval_viewer === 'true';
            document.getElementById('auto-approval-analyst').checked = 
                settings.auto_approval_analyst === 'true';
            document.getElementById('auto-approval-editor').checked = 
                settings.auto_approval_editor === 'true';
            
            // 시스템 매개변수
            document.getElementById('notification-batch-size').value = 
                settings.notification_batch_size || '50';
            document.getElementById('max-extension-count').value = 
                settings.max_extension_count || '3';
            document.getElementById('system-email').value = 
                displayMultipleEmails(settings.system_email || '');
        }
    } catch (error) {
        console.error('시스템 설정 로드 실패:', error);
        showAlert('시스템 설정을 불러오는데 실패했습니다.', 'danger');
    }
}

async function saveSystemSettings() {
    // 시스템 이메일 유효성 검사 및 정리
    const systemEmailValue = document.getElementById('system-email').value;
    const processedEmails = processMultipleEmails(systemEmailValue);
    
    if (!processedEmails.valid) {
        showAlert(processedEmails.error, 'danger');
        return;
    }
    
    const settings = {
        auto_approval_viewer: document.getElementById('auto-approval-viewer').checked.toString(),
        auto_approval_analyst: document.getElementById('auto-approval-analyst').checked.toString(),
        auto_approval_editor: document.getElementById('auto-approval-editor').checked.toString(),
        notification_batch_size: document.getElementById('notification-batch-size').value,
        max_extension_count: document.getElementById('max-extension-count').value,
        system_email: processedEmails.emails
    };
    
    try {
        const response = await fetch('/api/admin/system-settings', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            const emailCount = processedEmails.count;
            showAlert(`시스템 설정이 저장되었습니다. (시스템 이메일 ${emailCount}개 등록)`, 'success');
        } else {
            showAlert(data.message || '저장에 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('시스템 설정 저장 실패:', error);
        showAlert('저장 중 오류가 발생했습니다.', 'danger');
    }
}

// 계정/프로퍼티 로드 함수들
async function loadAccounts() {
    try {
        const response = await fetch('/api/accounts');
        const data = await response.json();
        
        if (data.success) {
            const selects = ['filter-account', 'manager-account'];
            selects.forEach(selectId => {
                const select = document.getElementById(selectId);
                // 기존 옵션 유지하고 새 옵션 추가
                data.accounts.forEach(account => {
                    const option = document.createElement('option');
                    option.value = account.id;
                    option.textContent = account.name;
                    select.appendChild(option);
                });
            });
        }
    } catch (error) {
        console.error('계정 로드 실패:', error);
    }
}

async function loadProperties() {
    try {
        const response = await fetch('/api/properties');
        const data = await response.json();
        
        if (data.success) {
            const selects = ['filter-property', 'manager-property'];
            selects.forEach(selectId => {
                const select = document.getElementById(selectId);
                // 기존 옵션 유지하고 새 옵션 추가
                data.properties.forEach(property => {
                    const option = document.createElement('option');
                    option.value = property.id;
                    option.textContent = property.name;
                    select.appendChild(option);
                });
            });
        }
    } catch (error) {
        console.error('프로퍼티 로드 실패:', error);
    }
}

// 여러 이메일 처리 함수
function processMultipleEmails(emailText) {
    if (!emailText || !emailText.trim()) {
        return { valid: false, error: '시스템 발송 이메일을 입력해주세요.' };
    }
    
    // 줄바꿈과 쉼표로 구분된 이메일들 분리
    const emails = emailText
        .split(/[\n,]/)  // 줄바꿈 또는 쉼표로 분리
        .map(email => email.trim())
        .filter(email => email.length > 0);
    
    if (emails.length === 0) {
        return { valid: false, error: '최소 하나의 이메일을 입력해주세요.' };
    }
    
    // 이메일 유효성 검사
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const invalidEmails = emails.filter(email => !emailRegex.test(email));
    
    if (invalidEmails.length > 0) {
        return { 
            valid: false, 
            error: `유효하지 않은 이메일 형식: ${invalidEmails.join(', ')}` 
        };
    }
    
    // 중복 제거
    const uniqueEmails = [...new Set(emails)];
    
    return {
        valid: true,
        emails: uniqueEmails.join(', '), // 쉼표로 구분하여 저장
        count: uniqueEmails.length
    };
}

function displayMultipleEmails(emailString) {
    if (!emailString) return '';
    
    // DB에서 쉼표로 구분된 이메일을 다시 줄바꿈으로 표시
    return emailString.split(',').map(email => email.trim()).join('\n');
}

// 유틸리티 함수들
function showAlert(message, type = 'info') {
    // 기존 알림 제거
    const existingAlert = document.querySelector('.alert-dismissible');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // 새 알림 생성
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 페이지 상단에 삽입
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 5초 후 자동 제거
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}