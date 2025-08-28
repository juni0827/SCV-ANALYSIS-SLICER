#!/usr/bin/env python3
"""
CSV Analyzer 빌드 스크립트
PyInstaller를 사용하여 Windows 실행 파일(.exe)을 생성합니다.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def cleanup_build_files():
    """이전 빌드 파일들 정리"""
    print("🧹 이전 빌드 파일 정리 중...")
    
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['*.spec']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   ✓ {dir_name} 폴더 제거")
    
    import glob
    for pattern in files_to_remove:
        for file in glob.glob(pattern):
            os.remove(file)
            print(f"   ✓ {file} 파일 제거")

def build_executable():
    """실행 파일 빌드"""
    print("🔨 CSV Analyzer 실행 파일 빌드 중...")
    print("   (이 과정은 수 분이 소요될 수 있습니다...)")
    
    # PyInstaller 명령어 구성
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',                    # 단일 실행 파일 생성
        '--windowed',                   # 콘솔 창 숨김
        '--name=CSV-Analyzer',          # 실행 파일 이름
        '--clean',                      # 캐시 정리
        
        # 불필요한 모듈 제외 (크기 최적화)
        '--exclude-module=dearpygui',
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6', 
        '--exclude-module=PySide2',
        '--exclude-module=PySide6',
        '--exclude-module=wx',
        '--exclude-module=test',
        '--exclude-module=unittest',
        
        # 최적화 옵션
        '--optimize=2',                 # 바이트코드 최적화
        '--strip',                      # 심볼 제거 (Unix/Linux)
        
        'app.py'                        # 메인 스크립트
    ]
    
    try:
        # 빌드 실행
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        print(f"표준 오류: {e.stderr}")
        return False

def check_result():
    """빌드 결과 확인"""
    exe_path = Path('dist/CSV-Analyzer.exe')
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n🎉 빌드 성공!")
        print(f"📁 생성된 파일: {exe_path}")
        print(f"📏 파일 크기: {size_mb:.1f} MB")
        
        # 실행 테스트 옵션
        choice = input("\n🚀 빌드된 실행 파일을 지금 테스트하시겠습니까? (y/n): ")
        if choice.lower() in ['y', 'yes']:
            os.startfile(str(exe_path))
        
        return True
    else:
        print("❌ 실행 파일이 생성되지 않았습니다.")
        return False

def main():
    """메인 함수"""
    print("=" * 50)
    print("       🔧 CSV Analyzer 빌드 도구 🔧")
    print("=" * 50)
    
    # 현재 디렉토리 확인
    if not Path('app.py').exists():
        print("❌ app.py 파일을 찾을 수 없습니다.")
        print("   이 스크립트를 app.py가 있는 폴더에서 실행하세요.")
        return False
    
    try:
        # 1. 정리
        cleanup_build_files()
        print()
        
        # 2. 빌드
        if not build_executable():
            return False
        
        # 3. 결과 확인
        return check_result()
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        input("\n❌ 빌드 실패. 엔터를 누르면 종료합니다...")
        sys.exit(1)
    else:
        input("\n✅ 빌드 완료. 엔터를 누르면 종료합니다...")
