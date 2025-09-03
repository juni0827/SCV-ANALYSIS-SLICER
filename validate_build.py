#!/usr/bin/env python3
"""
빌드 설정 검증 스크립트
실제 빌드 없이 설정이 올바른지 확인합니다.
"""

import sys
import importlib.util
from pathlib import Path

def test_build_prerequisites():
    """빌드 전제 조건 테스트"""
    print("=== 빌드 전제 조건 검증 ===")
    
    success = True
    
    # 1. 필수 파일 존재 확인
    required_files = [
        'app.py',
        'single_instance.py',
        'requirements.txt',
        'build.py',
        'build.bat',
        'csv_analyzer.spec'
    ]
    
    print("1. 필수 파일 확인:")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - 파일이 없습니다!")
            success = False
    
    # 2. 모듈 임포트 테스트
    print("\n2. 모듈 임포트 테스트:")
    test_modules = [
        ('single_instance', 'single_instance.py'),
        ('pandas', '설치된 패키지'),
        ('numpy', '설치된 패키지'),
        ('matplotlib', '설치된 패키지'),
    ]
    
    for module_name, source in test_modules:
        try:
            if module_name == 'single_instance':
                spec = importlib.util.spec_from_file_location(module_name, module_name + '.py')
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                importlib.import_module(module_name)
            print(f"   ✅ {module_name} ({source})")
        except Exception as e:
            print(f"   ❌ {module_name} - {e}")
            success = False
    
    # 3. PyInstaller 확인
    print("\n3. PyInstaller 확인:")
    try:
        import PyInstaller
        print(f"   ✅ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("   ❌ PyInstaller가 설치되지 않았습니다")
        success = False
    
    # 4. 단일 인스턴스 기능 테스트
    print("\n4. 단일 인스턴스 기능 테스트:")
    try:
        from single_instance import SingleInstanceManager
        manager = SingleInstanceManager("Test-App", show_message=False)
        is_running = manager.is_another_instance_running()
        manager.cleanup()
        print(f"   ✅ 단일 인스턴스 로직 동작: {not is_running}")
    except Exception as e:
        print(f"   ❌ 단일 인스턴스 테스트 실패: {e}")
        success = False
    
    # 5. 빌드 스펙 파일 검증
    print("\n5. PyInstaller 스펙 파일 검증:")
    try:
        with open('csv_analyzer.spec', 'r', encoding='utf-8') as f:
            spec_content = f.read()
            
        required_in_spec = [
            'single_instance',
            'ctypes',
            'app.py',
            'console=False'
        ]
        
        for item in required_in_spec:
            if item in spec_content:
                print(f"   ✅ {item} 포함됨")
            else:
                print(f"   ❌ {item} 누락됨")
                success = False
                
    except Exception as e:
        print(f"   ❌ 스펙 파일 검증 실패: {e}")
        success = False
    
    return success

def test_app_integration():
    """앱 통합 테스트 (GUI 없이)"""
    print("\n=== 앱 통합 테스트 ===")
    
    try:
        # app.py에서 단일 인스턴스 임포트가 제대로 되는지 확인
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        if 'from single_instance import check_single_instance' in app_content:
            print("   ✅ app.py에 단일 인스턴스 임포트 포함됨")
        else:
            print("   ❌ app.py에 단일 인스턴스 임포트 누락됨")
            return False
        
        if 'instance_manager = check_single_instance' in app_content:
            print("   ✅ app.py에 단일 인스턴스 체크 로직 포함됨")
        else:
            print("   ❌ app.py에 단일 인스턴스 체크 로직 누락됨")
            return False
        
        if 'instance_manager.cleanup()' in app_content:
            print("   ✅ app.py에 리소스 정리 로직 포함됨")
        else:
            print("   ❌ app.py에 리소스 정리 로직 누락됨")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 앱 통합 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("CSV Analyzer 단일 인스턴스 빌드 설정 검증\n")
    
    test1_passed = test_build_prerequisites()
    test2_passed = test_app_integration()
    
    print("\n" + "="*60)
    print("검증 결과:")
    print(f"  빌드 전제 조건:   {'✅ 통과' if test1_passed else '❌ 실패'}")
    print(f"  앱 통합:         {'✅ 통과' if test2_passed else '❌ 실패'}")
    
    all_passed = test1_passed and test2_passed
    
    if all_passed:
        print(f"\n✅ 모든 검증 통과!")
        print("🔨 실제 빌드를 위해 다음 명령을 실행하세요:")
        print("   Windows: build.bat")
        print("   Python:  python build.py")
    else:
        print(f"\n❌ 일부 검증 실패!")
        print("   위의 오류를 해결한 후 다시 시도하세요.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)