/**
 * 시스템 설정 관리 모듈
 * =====================
 * 
 * 시스템 설정 및 알림 설정 관련 기능을 담당
 */

class SystemSettingsManager {
    constructor() {
        this.currentSettings = {};
    }

    // 초기화
    async initialize() {
        await this.loadSystemSettings();
        await this.loadNotificationSettings();
        this.setupEventListeners();
    }

    // 이벤트 리스너 설정
    setupEventListeners() {
        // 알림 토글 이벤트 (이벤트 위임)
        document.addEventListener('change', (event) => {
            if (event.target.classList.contains('notification-toggle')) {
                const notificationType = event.target.dataset.notificationType;
                const isEnabled = event.target.checked;
                this.toggleNotification(notificationType, isEnabled);
            }
        });

        // 발송 기간 변경 이벤트 (이벤트 위임)
        document.addEventListener('change', (event) => {
            if (event.target.classList.contains('trigger-days')) {
                const notificationType = event.target.dataset.notificationType;
                const value = event.target.value;
                this.updateTriggerDays(notificationType, value);
            }
        });

        // 템플릿 편집 버튼 이벤트 (이벤트 위임)
        document.addEventListener('click', (event) => {
            if (event.target.closest('.edit-template-btn')) {
                const button = event.target.closest('.edit-template-btn');
                const notificationType = button.dataset.notificationType;
                this.editNotificationTemplate(notificationType);
            }
        });
    }

    // 시스템 설정 로드
    async loadSystemSettings() {
        try {
            const response = await fetch('/api/admin/system-settings');
            const data = await response.json();
            
            if (data.success) {
                this.currentSettings = data.settings;
                this.displaySystemSettings(data.settings);
            } else {
                AdminUtils.showAlert('시스템 설정을 불러오는데 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('시스템 설정 로드 실패:', error);
            AdminUtils.showAlert('시스템 설정을 불러오는데 실패했습니다.', 'danger');
        }
    }

    // 시스템 설정 표시
    displaySystemSettings(settings) {
        AdminUtils.setCheckboxValue('auto-approval-viewer', settings.auto_approval_viewer === 'true');
        AdminUtils.setCheckboxValue('auto-approval-analyst', settings.auto_approval_analyst === 'true');
        AdminUtils.setCheckboxValue('auto-approval-editor', settings.auto_approval_editor === 'true');
        AdminUtils.setElementValue('notification-batch-size', settings.notification_batch_size || '50');
        AdminUtils.setElementValue('max-extension-count', settings.max_extension_count || '3');
        
        // 여러 이메일 표시
        const systemEmailElement = document.getElementById('system-email');
        if (systemEmailElement) {
            systemEmailElement.value = AdminUtils.displayMultipleEmails(settings.system_email || '');
        }
    }

    // 시스템 설정 저장
    async saveSystemSettings() {
        // 시스템 이메일 유효성 검사 및 정리
        const systemEmailValue = document.getElementById('system-email').value;
        const processedEmails = AdminUtils.processMultipleEmails(systemEmailValue);
        
        if (!processedEmails.valid) {
            AdminUtils.showAlert(processedEmails.error, 'danger');
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
                AdminUtils.showAlert(`시스템 설정이 저장되었습니다. (시스템 이메일 ${emailCount}개 등록)`, 'success');
                this.currentSettings = { ...this.currentSettings, ...settings };
            } else {
                AdminUtils.showAlert(data.message || '저장에 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('시스템 설정 저장 실패:', error);
            AdminUtils.showAlert('저장 중 오류가 발생했습니다.', 'danger');
        }
    }

    // 알림 설정 로드
    async loadNotificationSettings() {
        try {
            const response = await fetch('/api/admin/notification-settings');
            const data = await response.json();
            
            if (data.success) {
                this.displayNotificationSettings(data.settings);
            } else {
                AdminUtils.showAlert('알림 설정을 불러오는데 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('알림 설정 로드 실패:', error);
            AdminUtils.showAlert('알림 설정을 불러오는데 실패했습니다.', 'danger');
        }
    }

    // 알림 설정 표시
    displayNotificationSettings(settings) {
        const tbody = document.getElementById('notifications-table');
        if (!tbody) {
            console.error('notifications-table 요소를 찾을 수 없습니다.');
            return;
        }
        
        tbody.innerHTML = '';
        
        settings.forEach(setting => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <strong>${this.getNotificationTypeName(setting.notification_type)}</strong>
                    <br><small class="text-muted">${this.getNotificationTypeDescription(setting.notification_type)}</small>
                </td>
                <td>
                    <div class="form-check form-switch">
                        <input class="form-check-input notification-toggle" type="checkbox" 
                               id="notify-${setting.notification_type}" 
                               data-notification-type="${setting.notification_type}"
                               ${setting.enabled ? 'checked' : ''}>
                    </div>
                </td>
                <td>
                    <input type="text" class="form-control form-control-sm trigger-days" 
                           value="${setting.trigger_days || '0'}"
                           placeholder="발송 기간 (예: 30,7,1)"
                           data-notification-type="${setting.notification_type}"
                           title="발송 기간을 쉼표로 구분하여 입력 (예: 30,7,1 = 30일전, 7일전, 1일전)">
                </td>
                <td>
                    <span class="text-muted small">템플릿 수정 불가</span>
                    <br>
                    <small class="text-success">${setting.template_subject || ''}</small>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-secondary" disabled>
                        <i class="fas fa-lock"></i> 고정
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // 알림 유형명 반환
    getNotificationTypeName(type) {
        const names = {
            'immediate_approval': '즉시 승인 알림',
            'daily_summary': '일일 요약 알림',
            'expiry_warning': '만료 경고 알림',
            'expiry_notice': '만료 통지 알림'
        };
        return names[type] || type;
    }

    // 알림 유형 설명 반환
    getNotificationTypeDescription(type) {
        const descriptions = {
            'immediate_approval': '권한 신청 시 즉시 담당자에게 알림',
            'daily_summary': '일일 권한 신청 요약 보고서',
            'expiry_warning': '권한 만료 예정 사전 알림',
            'expiry_notice': '권한 만료 당일 최종 알림'
        };
        return descriptions[type] || '';
    }

    // 알림 활성화/비활성화 토글
    async toggleNotification(notificationType, isEnabled) {
        try {
            const response = await fetch(`/api/admin/notification-settings/${notificationType}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ enabled: isEnabled })
            });

            const data = await response.json();

            if (data.success) {
                AdminUtils.showAlert(`${this.getNotificationTypeName(notificationType)} 알림이 ${isEnabled ? '활성화' : '비활성화'}되었습니다.`, 'success');
            } else {
                AdminUtils.showAlert('알림 설정 변경에 실패했습니다.', 'danger');
                // 체크박스 상태 되돌리기
                document.getElementById(`notify-${notificationType}`).checked = !isEnabled;
            }
        } catch (error) {
            console.error('알림 설정 변경 실패:', error);
            AdminUtils.showAlert('알림 설정 변경 중 오류가 발생했습니다.', 'danger');
            // 체크박스 상태 되돌리기
            document.getElementById(`notify-${notificationType}`).checked = !isEnabled;
        }
    }

    // 알림 템플릿 업데이트
    async updateNotificationTemplate(notificationType, field, value) {
        try {
            const response = await fetch(`/api/admin/notification-settings/${notificationType}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ [`template_${field}`]: value })
            });

            const data = await response.json();

            if (data.success) {
                console.log(`${field} 템플릿이 업데이트되었습니다.`);
            } else {
                AdminUtils.showAlert('템플릿 업데이트에 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('템플릿 업데이트 실패:', error);
            AdminUtils.showAlert('템플릿 업데이트 중 오류가 발생했습니다.', 'danger');
        }
    }

    // 발송 기간 업데이트
    async updateTriggerDays(notificationType, triggerDays) {
        // 유효성 검사
        if (!this.validateTriggerDays(triggerDays)) {
            AdminUtils.showAlert('올바른 발송 기간 형식이 아닙니다. (예: 30,7,1 또는 0)', 'warning');
            // 원래 값으로 되돌리기
            await this.loadNotificationSettings();
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/notification-settings/${notificationType}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ trigger_days: triggerDays })
            });

            const data = await response.json();

            if (data.success) {
                AdminUtils.showAlert(`${this.getNotificationTypeName(notificationType)} 발송 기간이 변경되었습니다.`, 'success');
            } else {
                AdminUtils.showAlert('발송 기간 변경에 실패했습니다.', 'danger');
                await this.loadNotificationSettings(); // 원래 값 복원
            }
        } catch (error) {
            console.error('발송 기간 변경 실패:', error);
            AdminUtils.showAlert('발송 기간 변경 중 오류가 발생했습니다.', 'danger');
            await this.loadNotificationSettings(); // 원래 값 복원
        }
    }

    // 발송 기간 유효성 검사
    validateTriggerDays(triggerDays) {
        if (!triggerDays || triggerDays.trim() === '') {
            return false;
        }
        
        // "0" (즉시) 또는 숫자,숫자,숫자 형태만 허용
        if (triggerDays === '0') {
            return true;
        }
        
        // 쉼표로 구분된 숫자들 검사
        const days = triggerDays.split(',');
        for (const day of days) {
            const num = parseInt(day.trim());
            if (isNaN(num) || num < 0) {
                return false;
            }
        }
        
        return true;
    }

    // 알림 템플릿 편집 (모달 또는 상세 페이지)
    editNotificationTemplate(notificationType) {
        AdminUtils.showAlert(`${this.getNotificationTypeName(notificationType)} 템플릿은 수정할 수 없습니다.`, 'info');
    }

    // 알림 일수 업데이트 (기존 함수 유지)
    async updateNotificationDays(notificationType, daysBefore) {
        const daysValue = parseInt(daysBefore) || 0;
        
        try {
            const response = await fetch(`/api/admin/notification-settings/${notificationType}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ days_before: daysValue })
            });

            const data = await response.json();

            if (data.success) {
                AdminUtils.showAlert(`${this.getNotificationTypeName(notificationType)} 알림 일수가 변경되었습니다.`, 'success');
            } else {
                AdminUtils.showAlert('알림 일수 변경에 실패했습니다.', 'danger');
            }
        } catch (error) {
            console.error('알림 일수 변경 실패:', error);
            AdminUtils.showAlert('알림 일수 변경 중 오류가 발생했습니다.', 'danger');
        }
    }
}

// 전역 인스턴스 생성
const systemSettingsManager = new SystemSettingsManager(); 