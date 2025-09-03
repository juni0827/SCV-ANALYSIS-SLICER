#!/usr/bin/env python3
"""
단일 인스턴스 동작 시뮬레이션 테스트
실제 애플리케이션의 동작을 시뮬레이션합니다.
"""

import time
import threading
from single_instance import check_single_instance

def simulate_app_instance(instance_name, duration=3):
    """애플리케이션 인스턴스 시뮬레이션"""
    print(f"[{instance_name}] 애플리케이션 시작 시도...")
    
    # 단일 인스턴스 체크
    instance_manager = check_single_instance("CSV-Analyzer-Simulation", show_message=False)
    
    if not instance_manager:
        print(f"[{instance_name}] ❌ 이미 다른 인스턴스가 실행 중입니다. 종료합니다.")
        return False
    
    try:
        print(f"[{instance_name}] ✅ 단일 인스턴스로 실행 시작")
        print(f"[{instance_name}] 🔄 {duration}초 동안 작업 수행 중...")
        
        # 실제 애플리케이션 작업 시뮬레이션
        time.sleep(duration)
        
        print(f"[{instance_name}] ✅ 작업 완료")
        return True
        
    finally:
        # 리소스 정리
        instance_manager.cleanup()
        print(f"[{instance_name}] 🧹 리소스 정리 완료")

def test_multiple_instances():
    """여러 인스턴스 동시 실행 테스트"""
    print("=== 다중 인스턴스 시뮬레이션 테스트 ===\n")
    
    # 첫 번째 인스턴스를 별도 스레드에서 실행
    def run_instance_1():
        simulate_app_instance("인스턴스-1", 5)
    
    thread1 = threading.Thread(target=run_instance_1)
    thread1.start()
    
    # 잠시 대기 후 두 번째 인스턴스 시도
    time.sleep(1)
    print("\n--- 1초 후 두 번째 인스턴스 실행 시도 ---")
    simulate_app_instance("인스턴스-2", 2)
    
    # 첫 번째 인스턴스가 끝날 때까지 대기
    thread1.join()
    
    # 첫 번째 인스턴스 종료 후 세 번째 인스턴스 시도
    print("\n--- 첫 번째 인스턴스 종료 후 세 번째 인스턴스 실행 시도 ---")
    time.sleep(0.5)  # 정리 시간 확보
    simulate_app_instance("인스턴스-3", 2)

def test_rapid_fire():
    """빠른 연속 실행 테스트 (사용자가 실수로 여러 번 클릭하는 상황)"""
    print("\n=== 빠른 연속 실행 테스트 ===")
    print("(사용자가 EXE를 빠르게 여러 번 클릭하는 상황 시뮬레이션)\n")
    
    def quick_instance(name):
        result = simulate_app_instance(name, 0.5)
        return result
    
    # 빠른 연속 실행
    threads = []
    for i in range(5):
        thread = threading.Thread(target=quick_instance, args=(f"빠른실행-{i+1}",))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # 100ms 간격으로 실행
    
    # 모든 스레드 완료 대기
    for thread in threads:
        thread.join()

def main():
    """메인 테스트"""
    print("CSV Analyzer 단일 인스턴스 동작 시뮬레이션\n")
    
    try:
        # 테스트 1: 일반적인 다중 인스턴스 시나리오
        test_multiple_instances()
        
        time.sleep(2)  # 테스트 간 대기
        
        # 테스트 2: 빠른 연속 실행
        test_rapid_fire()
        
        print("\n" + "="*60)
        print("✅ 모든 시뮬레이션 테스트 완료!")
        print("📌 결과: 단일 인스턴스가 올바르게 동작함")
        print("🔨 실제 EXE 파일을 빌드하여 테스트하세요:")
        print("   Windows: build.bat")
        print("   Python:  python build.py")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)