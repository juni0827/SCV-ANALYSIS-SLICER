#!/usr/bin/env python3
"""
최적화된 CSV Analyzer 빌드 스크립트
불필요한 라이브러리를 제외하여 빌드 시간과 파일 크기를 줄입니다.
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

def cleanup_build_files():
    """이전 빌드 파일들을 정리합니다."""
    print("🧹 이전 빌드 파일 정리 중...")
    
    files_to_remove = ["build", "dist", "CSV-Analyzer.spec", "__pycache__"]
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"   ✓ {file_path} 폴더 제거")
            else:
                os.remove(file_path)
                print(f"   ✓ {file_path} 파일 제거")

def check_dependencies():
    """필요한 종속성을 확인합니다."""
    try:
        import PyInstaller
        print(f"   ✓ PyInstaller {PyInstaller.__version__} 설치됨")
        return True
    except ImportError:
        print("   ❌ PyInstaller가 설치되지 않았습니다.")
        response = input("PyInstaller를 설치하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
            return True
        return False

def build_executable():
    """최적화된 실행 파일을 빌드합니다."""
    print("🔨 최적화된 CSV Analyzer 실행 파일 빌드 중...")
    print("   (torch, tensorflow 등 불필요한 라이브러리 제외)")
    
    # PyInstaller 명령어 구성
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # 단일 파일로 빌드
        "--windowed",                   # 콘솔 창 숨김
        "--name=CSV-Analyzer",          # 실행 파일 이름
        "--optimize=2",                 # 최적화 레벨 2
        
        # 불필요한 모듈들 제외하여 크기 줄이기
        "--exclude-module=torch",
        "--exclude-module=torchvision", 
        "--exclude-module=tensorflow",
        "--exclude-module=keras",
        "--exclude-module=sklearn",
        "--exclude-module=scipy.spatial.distance",
        "--exclude-module=PyQt5",
        "--exclude-module=PyQt6",
        "--exclude-module=PySide2",
        "--exclude-module=PySide6",
        "--exclude-module=tkinter",
        "--exclude-module=wx",
        
        # 테스트 모듈들 제외
        "--exclude-module=pytest",
        "--exclude-module=unittest",
        "--exclude-module=test",
        
        # 개발 도구들 제외
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "--exclude-module=notebook",
        
        "app.py"
    ]
    
    print("   실행 명령어:")
    print("  ", " ".join(cmd))
    print()
    
    try:
        # 빌드 실행
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ 빌드 성공!")
            return True
        else:
            print("   ❌ 빌드 실패!")
            print("   오류 출력:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"   ❌ 빌드 중 오류 발생: {e}")
        return False

def check_result():
    """빌드 결과를 확인합니다."""
    exe_path = Path("dist/CSV-Analyzer.exe")
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # MB 단위
        print(f"   ✅ 실행 파일 생성 완료: {exe_path}")
        print(f"   📦 파일 크기: {file_size:.1f} MB")
        
        print("\n🎉 빌드 완료!")
        print(f"   실행 파일 위치: {exe_path.absolute()}")
        print("   실행하려면 dist/CSV-Analyzer.exe를 더블클릭하세요.")
        
        return True
    else:
        print("   ❌ 실행 파일을 찾을 수 없습니다.")
        return False

def main():
    """메인 함수"""
    print("=" * 60)
    print("       🚀 CSV Analyzer 최적화 빌드 도구 🚀")
    print("=" * 60)
    
    start_time = time.time()
    
    # 1. 이전 빌드 파일 정리
    cleanup_build_files()
    print()
    
    # 2. 종속성 확인
    if not check_dependencies():
        print("종속성 설치를 완료한 후 다시 실행해주세요.")
        return False
    print()
    
    # 3. 실행 파일 빌드
    if not build_executable():
        print("빌드에 실패했습니다.")
        return False
    print()
    
    # 4. 결과 확인
    if not check_result():
        return False
    
    end_time = time.time()
    build_time = end_time - start_time
    print(f"\n⏱️  총 빌드 시간: {build_time:.1f}초")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
