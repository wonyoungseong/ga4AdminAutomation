/**
 * Admin 메인 관리자
 * =================
 * 
 * Facade 패턴을 적용하여 모든 Admin 모듈을 통합 관리
 */

class AdminManager {
    constructor() {
        this.modules = {
            validityPeriods: null,
            responsiblePersons: null,
            systemSettings: null
        };
        this.isInitialized = false;
    }

    // 전체 초기화
    async initialize() {
        if (this.isInitialized) return;

        try {
            console.log('🚀 Admin 모듈 초기화 시작');
            
            // 의존성 주입 방식으로 모듈 초기화
            this.modules.validityPeriods = validityPeriodsManager;
            this.modules.responsiblePersons = responsiblePersonsManager;
            this.modules.systemSettings = systemSettingsManager;

            // 모든 모듈 비동기 초기화
            const initPromises = [
                this.modules.validityPeriods.initialize(),
                this.modules.responsiblePersons.initialize(),
                this.modules.systemSettings.initialize()
            ];

            await Promise.all(initPromises);
            
            // 탭 이벤트 초기화
            this.initializeTabEvents();
            
            // 버튼 이벤트 바인딩
            this.bindEventListeners();
            
            this.isInitialized = true;
            console.log('✅ Admin 모듈 초기화 완료');
            
            AdminUtils.showAlert('관리자 페이지가 로드되었습니다.', 'success');
            
        } catch (error) {
            console.error('❌ Admin 모듈 초기화 실패:', error);
            AdminUtils.showAlert('관리자 페이지 로드 중 오류가 발생했습니다.', 'danger');
        }
    }

    // 탭 이벤트 초기화
    initializeTabEvents() {
        document.addEventListener('click', (event) => {
            // 탭 클릭 시 해당 모듈 새로고침
            if (event.target.matches('[data-bs-toggle="tab"]')) {
                const targetTab = event.target.getAttribute('data-bs-target');
                
                setTimeout(() => {
                    this.refreshTabContent(targetTab);
                }, 100);
            }
        });
    }

    // 버튼 이벤트 리스너 바인딩
    bindEventListeners() {
        console.log('🎯 이벤트 리스너 바인딩 시작');
        
        // 유효기간 관련 버튼
        const addPeriodBtn = document.getElementById('add-new-period-btn');
        if (addPeriodBtn) {
            addPeriodBtn.addEventListener('click', () => {
                this.modules.validityPeriods.addNewPeriod();
            });
            console.log('✅ 유효기간 추가 버튼 바인딩 완료');
        }
        
        const savePeriodBtn = document.getElementById('save-period-btn');
        if (savePeriodBtn) {
            savePeriodBtn.addEventListener('click', () => {
                this.modules.validityPeriods.savePeriod();
            });
            console.log('✅ 유효기간 저장 버튼 바인딩 완료');
        }
        
        // 담당자 관련 버튼
        const addManagerBtn = document.getElementById('add-new-manager-btn');
        if (addManagerBtn) {
            addManagerBtn.addEventListener('click', () => {
                this.modules.responsiblePersons.addNewManager();
            });
            console.log('✅ 담당자 추가 버튼 바인딩 완료');
        }
        
        const saveManagerBtn = document.getElementById('save-manager-btn');
        if (saveManagerBtn) {
            saveManagerBtn.addEventListener('click', () => {
                this.modules.responsiblePersons.saveManager();
            });
            console.log('✅ 담당자 저장 버튼 바인딩 완료');
        }
        
        // 시스템 설정 버튼
        const saveSystemBtn = document.getElementById('save-system-settings-btn');
        if (saveSystemBtn) {
            saveSystemBtn.addEventListener('click', () => {
                this.modules.systemSettings.saveSystemSettings();
            });
            console.log('✅ 시스템 설정 저장 버튼 바인딩 완료');
        }
        
        console.log('✅ 모든 이벤트 리스너 바인딩 완료');
    }

    // 탭 콘텐츠 새로고침
    async refreshTabContent(tabId) {
        try {
            switch (tabId) {
                case '#periods':
                    await this.modules.validityPeriods.loadValidityPeriods();
                    break;
                case '#managers':
                    await this.modules.responsiblePersons.loadResponsiblePersons();
                    break;
                case '#system':
                    await this.modules.systemSettings.loadSystemSettings();
                    await this.modules.systemSettings.loadNotificationSettings();
                    break;
            }
        } catch (error) {
            console.error('탭 새로고침 실패:', error);
        }
    }

    // 전체 데이터 새로고침
    async refreshAll() {
        AdminUtils.showLoading(true);
        
        try {
            await Promise.all([
                this.modules.validityPeriods.loadValidityPeriods(),
                this.modules.responsiblePersons.loadResponsiblePersons(),
                this.modules.systemSettings.loadSystemSettings(),
                this.modules.systemSettings.loadNotificationSettings()
            ]);
            
            AdminUtils.showAlert('모든 데이터가 새로고침되었습니다.', 'success');
        } catch (error) {
            console.error('전체 새로고침 실패:', error);
            AdminUtils.showAlert('데이터 새로고침 중 오류가 발생했습니다.', 'danger');
        } finally {
            AdminUtils.showLoading(false);
        }
    }

    // 특정 모듈 인스턴스 반환
    getModule(moduleName) {
        return this.modules[moduleName];
    }

    // 상태 확인
    getStatus() {
        return {
            initialized: this.isInitialized,
            modules: Object.keys(this.modules),
            moduleStatus: Object.fromEntries(
                Object.entries(this.modules).map(([key, module]) => [
                    key, 
                    module ? 'loaded' : 'not_loaded'
                ])
            )
        };
    }
}

// 전역 Admin Manager 인스턴스
const adminManager = new AdminManager();

// DOM이 로드되면 자동 초기화
document.addEventListener('DOMContentLoaded', () => {
    adminManager.initialize();
});

// 전역 함수로 노출 (HTML onClick 이벤트용)
window.adminManager = adminManager;

// 개별 모듈들도 전역 접근 가능하도록 유지 (하위 호환성)
window.validityPeriodsManager = validityPeriodsManager;
window.responsiblePersonsManager = responsiblePersonsManager;
window.systemSettingsManager = systemSettingsManager; 