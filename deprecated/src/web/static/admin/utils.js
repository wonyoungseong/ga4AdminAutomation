/**
 * Admin 공통 유틸리티 모듈
 * =========================
 * 
 * DRY 원칙에 따라 공통 기능을 재사용 가능하게 구성
 */

class AdminUtils {
    // 알림 표시
    static showAlert(message, type = 'info') {
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
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }
        
        // 5초 후 자동 제거
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // 여러 이메일 처리 함수
    static processMultipleEmails(emailText) {
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

    // 여러 이메일 표시 형식 변환
    static displayMultipleEmails(emailString) {
        if (!emailString) return '';
        
        // DB에서 쉼표로 구분된 이메일을 다시 줄바꿈으로 표시
        return emailString.split(',').map(email => email.trim()).join('\n');
    }

    // 안전한 DOM 요소 값 설정
    static setElementValue(elementId, value, defaultValue = '') {
        const element = document.getElementById(elementId);
        if (element) {
            element.value = value || defaultValue;
        }
    }

    // 안전한 체크박스 설정
    static setCheckboxValue(elementId, checked) {
        const element = document.getElementById(elementId);
        if (element) {
            element.checked = !!checked;
        }
    }

    // API 호출 공통 함수
    static async apiCall(url, options = {}) {
        try {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            const mergedOptions = { ...defaultOptions, ...options };
            const response = await fetch(url, mergedOptions);
            const data = await response.json();
            
            return {
                success: response.ok,
                status: response.status,
                data: data
            };
        } catch (error) {
            console.error('API 호출 실패:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // 로딩 스피너 표시/숨김
    static showLoading(show = true) {
        const loadingEl = document.getElementById('loading-spinner');
        if (loadingEl) {
            loadingEl.style.display = show ? 'block' : 'none';
        }
    }

    // 폼 검증
    static validateForm(formId, requiredFields) {
        const form = document.getElementById(formId);
        if (!form) return false;

        for (const fieldId of requiredFields) {
            const field = document.getElementById(fieldId);
            if (!field || !field.value.trim()) {
                AdminUtils.showAlert(`${field?.placeholder || fieldId} 필드를 입력해주세요.`, 'warning');
                field?.focus();
                return false;
            }
        }
        return true;
    }

    // 날짜 포맷팅
    static formatDate(dateString) {
        if (!dateString) return '-';
        
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // 숫자 포맷팅 (콤마 추가)
    static formatNumber(number) {
        if (number === null || number === undefined) return '0';
        return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    // 디바운스 함수
    static debounce(func, wait) {
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
} 