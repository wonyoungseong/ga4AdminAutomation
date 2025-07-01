import json
import os
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding, CreateAccessBindingRequest
from google.oauth2 import service_account

# Service Account 인증 파일 경로
SERVICE_ACCOUNT_FILE = 'ga4-automatio-797ec352f393.json'

# 필요한 스코프
SCOPES = ['https://www.googleapis.com/auth/analytics.manage.users']

def authenticate_google_api():
    """
    Service Account를 사용한 Google Analytics Admin API 인증
    """
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"❌ Error: {SERVICE_ACCOUNT_FILE} 파일을 찾을 수 없습니다.")
            return None
        
        # Service Account 자격 증명 로드
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES
        )
        
        print("✅ Service Account 인증 성공")
        return credentials
        
    except Exception as e:
        print(f"❌ 인증 오류: {e}")
        return None

def add_user_to_ga4_property(account_id, property_id, user_email, role='analyst'):
    """
    GA4 속성에 사용자 추가 (Alpha API의 accessBindings 사용)
    """
    # API 인증
    creds = authenticate_google_api()
    if not creds:
        return False
    
    # Analytics Admin API 클라이언트 생성 (Alpha 버전)
    client = AnalyticsAdminServiceClient(credentials=creds)
    
    try:
        # 속성 경로 생성
        parent = f"properties/{property_id}"
        
        print(f"속성 경로: {parent}")
        print(f"추가할 사용자: {user_email}")
        print(f"역할: {role}")
        
        # 역할 매핑
        role_mapping = {
            'analyst': 'predefinedRoles/analyst',
            'editor': 'predefinedRoles/editor', 
            'admin': 'predefinedRoles/admin',
            'viewer': 'predefinedRoles/viewer'
        }
        
        predefined_role = role_mapping.get(role.lower(), 'predefinedRoles/analyst')
        
        # AccessBinding 생성
        access_binding = AccessBinding(
            user=user_email,
            roles=[predefined_role]
        )
        
        # CreateAccessBindingRequest 생성
        request = CreateAccessBindingRequest(
            parent=parent,
            access_binding=access_binding
        )
        
        print(f"요청 생성 완료:")
        print(f"  - Parent: {parent}")
        print(f"  - User: {user_email}")
        print(f"  - Role: {predefined_role}")
        
        # API 호출
        response = client.create_access_binding(request=request)
        
        print(f"✅ 사용자 추가 성공!")
        print(f"응답: {response}")
        return True
        
    except Exception as e:
        print(f"❌ 사용자 추가 중 오류 발생: {e}")
        print(f"   - 오류 타입: {type(e).__name__}")
        
        # 일반적인 오류 원인 안내
        if "PERMISSION_DENIED" in str(e):
            print("   - 권한 오류: Service Account에 GA4 속성 관리 권한이 없습니다.")
            print("   - 해결방법: GA4에서 Service Account 이메일을 관리자로 추가해주세요.")
            print(f"   - Service Account 이메일: ga4-automation-test@ga4-automatio.iam.gserviceaccount.com")
        elif "NOT_FOUND" in str(e):
            print("   - 속성을 찾을 수 없습니다. 속성 ID를 확인해주세요.")
        elif "ALREADY_EXISTS" in str(e):
            print("   - 해당 사용자가 이미 속성에 추가되어 있습니다.")
        elif "INVALID_ARGUMENT" in str(e):
            print("   - 잘못된 인수입니다. 이메일 주소나 역할을 확인해주세요.")
        
        return False

def remove_user_from_ga4_property(property_id, user_email):
    """
    GA4 속성에서 사용자 제거 (Alpha API의 accessBindings 사용)
    """
    # API 인증
    creds = authenticate_google_api()
    if not creds:
        return False
    
    # Analytics Admin API 클라이언트 생성 (Alpha 버전)
    client = AnalyticsAdminServiceClient(credentials=creds)
    
    try:
        parent = f"properties/{property_id}"
        
        print(f"속성 경로: {parent}")
        print(f"제거할 사용자: {user_email}")
        
        # 먼저 기존 access bindings 조회하여 해당 사용자의 binding name 찾기
        response = client.list_access_bindings(parent=parent)
        
        user_binding_name = None
        for binding in response:
            if binding.user == user_email:
                user_binding_name = binding.name
                print(f"찾은 사용자 바인딩: {user_binding_name}")
                print(f"현재 역할: {', '.join(binding.roles)}")
                break
        
        if not user_binding_name:
            print(f"❌ 사용자 '{user_email}'를 속성에서 찾을 수 없습니다.")
            return False
        
        # Access binding 삭제
        client.delete_access_binding(name=user_binding_name)
        
        print(f"✅ 사용자 제거 성공!")
        print(f"제거된 사용자: {user_email}")
        return True
        
    except Exception as e:
        print(f"❌ 사용자 제거 중 오류 발생: {e}")
        print(f"   - 오류 타입: {type(e).__name__}")
        
        # 일반적인 오류 원인 안내
        if "PERMISSION_DENIED" in str(e):
            print("   - 권한 오류: Service Account에 GA4 속성 관리 권한이 없습니다.")
        elif "NOT_FOUND" in str(e):
            print("   - 사용자를 찾을 수 없거나 속성 ID가 잘못되었습니다.")
        
        return False

def list_existing_users(property_id):
    """
    속성의 기존 사용자 목록 조회
    """
    creds = authenticate_google_api()
    if not creds:
        return []
    
    client = AnalyticsAdminServiceClient(credentials=creds)
    
    try:
        parent = f"properties/{property_id}"
        
        # 기존 access bindings 조회
        response = client.list_access_bindings(parent=parent)
        
        print(f"\n📋 현재 사용자 목록:")
        users = []
        for i, binding in enumerate(response, 1):
            users.append({
                'user': binding.user,
                'roles': list(binding.roles),
                'binding_name': binding.name
            })
            print(f"  {i}. 사용자: {binding.user}")
            print(f"     역할: {', '.join(binding.roles)}")
        
        if not users:
            print("  (사용자가 없습니다)")
        
        return users
        
    except Exception as e:
        print(f"❌ 사용자 목록 조회 오류: {e}")
        return []

def interactive_user_removal(property_id):
    """
    대화형 사용자 제거 인터페이스
    """
    print("\n=== 사용자 제거 ===")
    
    # 현재 사용자 목록 조회
    users = list_existing_users(property_id)
    
    if not users:
        print("제거할 사용자가 없습니다.")
        return False
    
    print(f"\n제거할 사용자를 선택하세요:")
    for i, user in enumerate(users, 1):
        print(f"  {i}. {user['user']} ({', '.join(user['roles'])})")
    
    try:
        choice = input(f"\n번호를 입력하세요 (1-{len(users)}) 또는 'q'로 취소: ").strip()
        
        if choice.lower() == 'q':
            print("취소되었습니다.")
            return False
        
        choice_num = int(choice)
        if 1 <= choice_num <= len(users):
            selected_user = users[choice_num - 1]
            user_email = selected_user['user']
            
            # 확인
            confirm = input(f"\n정말로 '{user_email}' 사용자를 제거하시겠습니까? (y/N): ").strip().lower()
            
            if confirm == 'y':
                return remove_user_from_ga4_property(property_id, user_email)
            else:
                print("취소되었습니다.")
                return False
        else:
            print("잘못된 번호입니다.")
            return False
            
    except ValueError:
        print("올바른 번호를 입력해주세요.")
        return False
    except KeyboardInterrupt:
        print("\n취소되었습니다.")
        return False

def show_menu():
    """
    메뉴 표시
    """
    print("\n" + "="*50)
    print("   GA4 사용자 관리 자동화")
    print("="*50)
    print("1. 사용자 추가")
    print("2. 사용자 제거")
    print("3. 사용자 목록 조회")
    print("4. 종료")
    print("="*50)

def main():
    """
    메인 함수
    """
    print("=== GA4 사용자 관리 자동화 (Alpha API accessBindings 방식) ===\n")
    
    # 설정 파일 로드
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Error: config.json 파일을 찾을 수 없습니다.")
        return
    
    account_id = config.get('account_id')
    property_id = config.get('property_id')
    
    if not all([account_id, property_id]):
        print("❌ Error: config.json에 account_id와 property_id가 필요합니다.")
        return
    
    print(f"설정 정보:")
    print(f"  - 계정 ID: {account_id}")
    print(f"  - 속성 ID: {property_id}")
    
    while True:
        show_menu()
        
        try:
            choice = input("\n선택하세요 (1-4): ").strip()
            
            if choice == '1':
                # 사용자 추가
                print("\n=== 사용자 추가 ===")
                new_user_email = config.get('new_user_email')
                new_user_role = config.get('role', 'Analyst')
                
                if not new_user_email:
                    new_user_email = input("추가할 사용자 이메일: ").strip()
                    if not new_user_email:
                        print("이메일을 입력해주세요.")
                        continue
                
                print(f"역할 선택 (현재: {new_user_role}):")
                print("1. Viewer")
                print("2. Analyst")
                print("3. Editor") 
                print("4. Admin")
                
                role_choice = input("역할 번호를 입력하거나 Enter로 기본값 사용: ").strip()
                role_mapping = {'1': 'viewer', '2': 'analyst', '3': 'editor', '4': 'admin'}
                
                if role_choice in role_mapping:
                    new_user_role = role_mapping[role_choice]
                
                print(f"\n추가할 사용자: {new_user_email}")
                print(f"역할: {new_user_role}")
                
                confirm = input("계속하시겠습니까? (y/N): ").strip().lower()
                if confirm == 'y':
                    success = add_user_to_ga4_property(account_id, property_id, new_user_email, new_user_role)
                    if success:
                        print("\n🎉 사용자 추가 완료!")
                    else:
                        print("\n💥 사용자 추가 실패!")
                
            elif choice == '2':
                # 사용자 제거
                success = interactive_user_removal(property_id)
                if success:
                    print("\n🎉 사용자 제거 완료!")
                else:
                    print("\n💥 사용자 제거 실패!")
                
            elif choice == '3':
                # 사용자 목록 조회
                print("\n=== 사용자 목록 조회 ===")
                list_existing_users(property_id)
                
            elif choice == '4':
                # 종료
                print("\n프로그램을 종료합니다.")
                break
                
            else:
                print("올바른 번호를 입력해주세요.")
                
        except KeyboardInterrupt:
            print("\n\n프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")

if __name__ == "__main__":
    main() 