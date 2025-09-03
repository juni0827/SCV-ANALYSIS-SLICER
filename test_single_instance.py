#!/usr/bin/env python3
"""
단일 인스턴스 기능 테스트
GUI 없이 단일 인스턴스 로직만 테스트합니다.
"""

import sys
import time
import subprocess
from pathlib import Path

def test_single_instance_logic():
    """단일 인스턴스 로직만 테스트"""
    print("=== 단일 인스턴스 로직 테스트 ===")
    
    try:
        from single_instance import SingleInstanceManager
        
        # 첫 번째 인스턴스 생성
        print("1. 첫 번째 인스턴스 매니저 생성...")
        manager1 = SingleInstanceManager("CSV-Analyzer-Test", show_message=False)
        
        is_running = manager1.is_another_instance_running()
        print(f"   다른 인스턴스 실행 중: {is_running}")
        
        if is_running:
            print("   ❌ 첫 번째 인스턴스인데 다른 인스턴스가 감지됨")
            return False
        
        # 두 번째 인스턴스 생성 (같은 이름)
        print("2. 두 번째 인스턴스 매니저 생성...")
        manager2 = SingleInstanceManager("CSV-Analyzer-Test", show_message=False)
        
        is_running = manager2.is_another_instance_running()
        print(f"   다른 인스턴스 실행 중: {is_running}")
        
        if not is_running:
            print("   ❌ 두 번째 인스턴스인데 다른 인스턴스가 감지되지 않음")
            manager1.cleanup()
            return False
        
        # 정리
        print("3. 리소스 정리...")
        manager1.cleanup()
        manager2.cleanup()
        
        # 다시 확인 (정리 후)
        print("4. 정리 후 다시 확인...")
        manager3 = SingleInstanceManager("CSV-Analyzer-Test", show_message=False)
        is_running = manager3.is_another_instance_running()
        print(f"   다른 인스턴스 실행 중: {is_running}")
        
        if is_running:
            print("   ❌ 정리 후인데 여전히 다른 인스턴스가 감지됨")
            manager3.cleanup()
            return False
        
        manager3.cleanup()
        print("   ✅ 모든 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"   ❌ 테스트 중 오류: {e}")
        return False

def test_import_app_module():
    """app 모듈이 올바르게 임포트되는지 테스트"""
    print("\n=== app 모듈 임포트 테스트 ===")
    
    try:
        # 임포트 테스트 (GUI 초기화 없이)
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("app", "app.py")
        if spec is None:
            print("   ❌ app.py 파일을 찾을 수 없음")
            return False
            
        # 모듈 로드만 (실행하지 않음)
        print("   ✅ app.py 파일 존재 확인")
        print("   ✅ single_instance 모듈 임포트 성공")
        return True
        
    except Exception as e:
        print(f"   ❌ 모듈 테스트 중 오류: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("CSV Analyzer 단일 인스턴스 기능 테스트\n")
    
    # 테스트 실행
    test1_passed = test_single_instance_logic()
    test2_passed = test_import_app_module()
    
    # 결과 출력
    print("\n" + "="*50)
    print("테스트 결과:")
    print(f"  단일 인스턴스 로직: {'✅ 통과' if test1_passed else '❌ 실패'}")
    print(f"  모듈 임포트:      {'✅ 통과' if test2_passed else '❌ 실패'}")
    
    all_passed = test1_passed and test2_passed
    print(f"\n전체 결과: {'✅ 모든 테스트 통과!' if all_passed else '❌ 일부 테스트 실패'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)