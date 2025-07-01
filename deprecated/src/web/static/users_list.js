// 사용자 목록 페이지 JavaScript

// 전역 변수
let currentPage = 1;
let currentFilters = {};
let totalPages = 1;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    loadAccounts();
    loadProperties();
    loadUsers();
    
    // 폼 제출 이벤트
    document.getElementById('filter-form').addEventListener('submit', function(e) {
        e.preventDefault();
        currentPage = 1;
        loadUsers();
    });
    
    // 필터 변경 시 실시간 업데이트
    const filterElements = ['status-filter', 'role-filter', 'account-filter', 'property-filter', 'start-date', 'end-date', 'search-input'];
    filterElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            element.addEventListener('change', function() {
                currentPage = 1;
                loadUsers();
            });
            
            // 검색 입력의 경우 키보드 입력도 처리
            if (elementId === 'search-input') {
                element.addEventListener('input', debounce(function() {
                    currentPage = 1;
                    loadUsers();
                }, 500));
            }
        }
    });
});

// 디바운스 함수 (검색 입력 최적화)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 계정 목록 로드
async function loadAccounts() {
    try {
        const response = await fetch('/api/accounts');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('account-filter');
            data.accounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;
                option.textContent = account.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('계정 목록 로드 실패:', error);
    }
}

// 프로퍼티 목록 로드
async function loadProperties() {
    try {
        const response = await fetch('/api/properties');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('property-filter');
            data.properties.forEach(property => {
                const option = document.createElement('option');
                option.value = property.property_id;
                option.textContent = property.property_display_name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('프로퍼티 목록 로드 실패:', error);
    }
}

// 사용자 목록 로드
async function loadUsers() {
    try {
        showLoading();
        
        // 필터 값 수집
        const formData = new FormData(document.getElementById('filter-form'));
        const params = new URLSearchParams();
        
        for (const [key, value] of formData.entries()) {
            if (value) {
                params.append(key, value);
            }
        }
        
        params.append('page', currentPage);
        params.append('per_page', 50);
        
        currentFilters = Object.fromEntries(params);
        
        const response = await fetch(`/api/users?${params}`);
        const data = await response.json();
        
        // 디버깅 로그 추가
        console.log('API 요청 URL:', `/api/users?${params}`);
        console.log('API 응답 데이터:', data);
        
        if (data.success) {
            // API 응답 구조에 맞게 안전하게 접근
            const responseData = data.data || data;
            const users = responseData.users || data.users || [];
            const pagination = responseData.pagination || data.pagination || {};
            
            console.log('처리된 사용자 데이터:', users);
            console.log('사용자 수:', users.length);
            
            displayUsers(users);
            updatePagination(pagination);
            updatePaginationInfo(pagination);
        } else {
            showError('사용자 목록을 불러오는데 실패했습니다.');
        }
    } catch (error) {
        console.error('사용자 목록 로드 실패:', error);
        showError('사용자 목록을 불러오는데 실패했습니다.');
    }
}

// 로딩 표시
function showLoading() {
    document.getElementById('users-table-body').innerHTML = `
        <tr>
            <td colspan="12" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">로딩 중...</span>
                </div>
                <div class="mt-2">데이터를 불러오는 중...</div>
            </td>
        </tr>
    `;
}

// 에러 표시
function showError(message) {
    document.getElementById('users-table-body').innerHTML = `
        <tr>
            <td colspan="12" class="text-center py-4 text-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>${message}
            </td>
        </tr>
    `;
}

// 사용자 목록 표시
function displayUsers(users) {
    const tbody = document.getElementById('users-table-body');
    
    console.log('displayUsers 호출됨, 사용자 수:', users ? users.length : 'null/undefined');
    console.log('사용자 데이터 샘플:', users ? users.slice(0, 2) : 'no data');
    
    if (!users || users.length === 0) {
        console.log('사용자가 없어서 빈 메시지 표시');
        tbody.innerHTML = `
            <tr>
                <td colspan="12" class="text-center py-4 text-muted">
                    <i class="fas fa-inbox me-2"></i>조건에 맞는 사용자가 없습니다.
                </td>
            </tr>
        `;
        return;
    }
    
    try {
        console.log('HTML 렌더링 시작, 첫 번째 사용자:', users[0]);
        
        const htmlContent = users.map((user, index) => {
            if (index < 3) {
                console.log(`사용자 ${index + 1} 렌더링:`, {
                    id: user.id,
                    applicant: user.applicant,
                    permission_level: user.permission_level,
                    status: user.status
                });
            }
            
            return `
                <tr>
                    <td>${user.id}</td>
                    <td>${user.applicant}</td>
                    <td>${user.user_email}</td>
                    <td>${user.property_name || user.property_id}</td>
                    <td>${user.account_name || '-'}</td>
                    <td>
                        <span class="badge permission-badge ${getPermissionBadgeClass(user.permission_level)}">
                            ${getPermissionDisplayName(user.permission_level)}
                        </span>
                    </td>
                    <td>
                        <span class="badge status-badge ${getStatusBadgeClass(user.status)}">
                            ${getStatusDisplayName(user.status)}
                        </span>
                    </td>
                    <td>
                        <span class="ga4-status ${user.ga4_registered ? 'text-success' : 'text-secondary'}">
                            <i class="fas ${user.ga4_registered ? 'fa-check-circle' : 'fa-times-circle'} me-1"></i>
                            ${user.ga4_registered ? '등록됨' : '미등록'}
                        </span>
                    </td>
                    <td>${formatDate(user.created_at)}</td>
                    <td>${formatDate(user.expiry_date)}</td>
                    <td>${user.extension_count || 0}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            ${getActionButtons(user)}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        console.log('HTML 생성 완료, 길이:', htmlContent.length);
        console.log('HTML 샘플 (처음 200자):', htmlContent.substring(0, 200));
        
        tbody.innerHTML = htmlContent;
        console.log('DOM 업데이트 완료');
        
        // DOM 업데이트 후 확인
        setTimeout(() => {
            const rowCount = tbody.querySelectorAll('tr').length;
            console.log('DOM에서 확인된 행 수:', rowCount);
        }, 100);
        
    } catch (error) {
        console.error('HTML 렌더링 중 오류:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="12" class="text-center py-4 text-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>렌더링 오류: ${error.message}
                </td>
            </tr>
        `;
    }
}

// 권한 배지 클래스
function getPermissionBadgeClass(permission) {
    const classes = {
        'viewer': 'bg-info',
        'analyst': 'bg-warning text-dark',
        'editor': 'bg-danger',
        'admin': 'bg-dark'
    };
    return classes[permission] || 'bg-secondary';
}

// 권한 표시명
function getPermissionDisplayName(permission) {
    const names = {
        'viewer': 'Viewer',
        'analyst': 'Analyst',
        'editor': 'Editor',
        'admin': 'Admin'
    };
    return names[permission] || permission;
}

// 상태 배지 클래스
function getStatusBadgeClass(status) {
    const classes = {
        'active': 'bg-success',
        'pending_approval': 'bg-warning text-dark',
        'expired': 'bg-secondary',
        'deleted': 'bg-dark'
    };
    return classes[status] || 'bg-secondary';
}

// 상태 표시명
function getStatusDisplayName(status) {
    const names = {
        'active': '활성',
        'pending_approval': '승인 대기',
        'expired': '만료',
        'deleted': '삭제'
    };
    return names[status] || status;
}

// 날짜 포맷
function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR');
    } catch {
        return dateString;
    }
}

// 액션 버튼
function getActionButtons(user) {
    let buttons = '';
    
    if (user.status === 'pending_approval') {
        buttons += `
            <button class="btn btn-success btn-sm" onclick="approveUser(${user.id})">
                <i class="fas fa-check"></i>
            </button>
            <button class="btn btn-danger btn-sm" onclick="rejectUser(${user.id})">
                <i class="fas fa-times"></i>
            </button>
        `;
    } else if (user.status === 'active') {
        buttons += `
            <button class="btn btn-warning btn-sm" onclick="extendUser(${user.id})">
                <i class="fas fa-clock"></i>
            </button>
            <button class="btn btn-danger btn-sm" onclick="deleteUser(${user.id})">
                <i class="fas fa-trash"></i>
            </button>
        `;
    }
    
    return buttons || '<span class="text-muted">-</span>';
}

// 페이지네이션 업데이트
function updatePagination(pagination) {
    const paginationEl = document.getElementById('pagination');
    
    // 안전한 pagination 접근
    if (!pagination || typeof pagination !== 'object') {
        paginationEl.innerHTML = '';
        return;
    }
    
    totalPages = pagination.total_pages || 1;
    
    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 이전 페이지
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">이전</a>
        </li>
    `;
    
    // 페이지 번호
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    // 다음 페이지
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">다음</a>
        </li>
    `;
    
    paginationEl.innerHTML = html;
}

// 페이지네이션 정보 업데이트
function updatePaginationInfo(pagination) {
    // 안전한 pagination 접근
    if (!pagination || typeof pagination !== 'object') {
        document.getElementById('pagination-info').textContent = '정보 없음';
        return;
    }
    
    const page = pagination.page || 1;
    const perPage = pagination.per_page || 50;
    const total = pagination.total || 0;
    
    const start = (page - 1) * perPage + 1;
    const end = Math.min(page * perPage, total);
    
    document.getElementById('pagination-info').textContent = 
        `전체 ${total}개 중 ${start}-${end}개 표시`;
}

// 페이지 변경
function changePage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadUsers();
}

// 필터 초기화
function resetFilters() {
    document.getElementById('filter-form').reset();
    currentPage = 1;
    loadUsers();
}

// CSV 내보내기
async function exportCSV() {
    try {
        const params = new URLSearchParams();
        
        // 현재 필터 조건 적용
        for (const [key, value] of Object.entries(currentFilters)) {
            if (value && key !== 'page' && key !== 'per_page') {
                params.append(key, value);
            }
        }
        
        const url = `/api/users/export?${params}`;
        window.open(url, '_blank');
        
        showAlert('CSV 파일 다운로드가 시작되었습니다.', 'success');
    } catch (error) {
        console.error('CSV 내보내기 실패:', error);
        showAlert('CSV 내보내기에 실패했습니다.', 'danger');
    }
}

// 사용자 승인
async function approveUser(id) {
    if (!confirm('이 사용자를 승인하시겠습니까?')) return;
    
    try {
        const response = await fetch(`/api/approve/${id}`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showAlert('사용자가 승인되었습니다.', 'success');
            loadUsers();
        } else {
            showAlert(data.message || '승인에 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('승인 실패:', error);
        showAlert('승인 중 오류가 발생했습니다.', 'danger');
    }
}

// 사용자 거부
async function rejectUser(id) {
    if (!confirm('이 사용자를 거부하시겠습니까?')) return;
    
    try {
        const response = await fetch(`/api/reject/${id}`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showAlert('사용자가 거부되었습니다.', 'success');
            loadUsers();
        } else {
            showAlert(data.message || '거부에 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('거부 실패:', error);
        showAlert('거부 중 오류가 발생했습니다.', 'danger');
    }
}

// 사용자 연장
async function extendUser(id) {
    if (!confirm('이 사용자의 권한을 연장하시겠습니까?')) return;
    
    try {
        const response = await fetch(`/api/extend/${id}`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showAlert('권한이 연장되었습니다.', 'success');
            loadUsers();
        } else {
            showAlert(data.message || '연장에 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('연장 실패:', error);
        showAlert('연장 중 오류가 발생했습니다.', 'danger');
    }
}

// 사용자 삭제
async function deleteUser(id) {
    if (!confirm('이 사용자를 삭제하시겠습니까?')) return;
    
    try {
        const response = await fetch(`/api/registration/${id}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            showAlert('사용자가 삭제되었습니다.', 'success');
            loadUsers();
        } else {
            showAlert(data.message || '삭제에 실패했습니다.', 'danger');
        }
    } catch (error) {
        console.error('삭제 실패:', error);
        showAlert('삭제 중 오류가 발생했습니다.', 'danger');
    }
}

// 알림 표시
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}