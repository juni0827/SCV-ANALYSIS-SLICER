#!/usr/bin/env python3
"""
CSV Analyzer 통합 빌드 스크립트
PyInstaller를 사용하여 크로스 플랫폼 실행 파일을 생성합니다.

사용법:
  python build.py              # 빌드 시작
  python build.py --clean      # 빌드 파일 정리만
  python build.py --help       # 도움말
"""

import os
import sys
import shutil
import subprocess
import platform
import time
from pathlib import Path
from typing import List, Dict, Any

class BuildConfig:
    """빌드 설정 클래스"""

    def __init__(self):
        self.name = "CSV-Analyzer"
        self.main_script = "src/gui/app.py"
        self.console = False
        self.onefile = True
        self.optimize = 1  # 기본 최적화 레벨

        # 플랫폼별 설정
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux"
        self.is_macos = platform.system() == "Darwin"

        # 제외할 모듈들
        self.exclude_modules = self._get_exclude_modules()

        # 추가 데이터 파일들
        self.datas = [
            ("README.md", "."),
            ("src/dsl/dsl_tokenizer.json", "src/dsl"),
            ("src/dsl/model.pt", "src/dsl"),
        ]

    def _get_exclude_modules(self) -> List[str]:
        """제외 모듈 목록"""
        return [
            'dearpygui',  # 사용하지 않는 GUI 라이브러리
            'PyQt5', 'PyQt6', 'PySide2', 'PySide6',  # Qt 라이브러리
            'wx',  # wxPython
            'tkinter',  # 표준 tkinter (dearpygui 사용)
            'test', 'unittest', 'pytest',  # 테스트 모듈들
            'IPython', 'jupyter', 'notebook',  # Jupyter 관련
        ]

    def get_pyinstaller_args(self) -> List[str]:
        """PyInstaller 명령어 인자 생성"""
        args = [
            sys.executable, '-m', 'PyInstaller',
            '--name', self.name,
            '--optimize', str(self.optimize),
        ]

        if self.onefile:
            args.append('--onefile')

        if not self.console:
            args.append('--windowed')

        # 제외 모듈들 추가
        for module in self.exclude_modules:
            args.extend(['--exclude-module', module])

        # 추가 데이터 파일들
        for src, dst in self.datas:
            if os.path.exists(src):
                # 플랫폼별 경로 구분자
                separator = ":" if not self.is_windows else ";"
                args.extend(['--add-data', f'{src}{separator}{dst}'])

        # 메인 스크립트
        args.append(self.main_script)

        return args

class BuildTool:
    """빌드 도구 클래스"""

    def __init__(self, config: BuildConfig):
        self.config = config

    def cleanup(self) -> bool:
        """이전 빌드 파일들 정리"""
        print("Cleaning up previous build files...")

        dirs_to_remove = ['build', 'dist', '__pycache__']
        files_to_remove = ['*.spec']

        success = True

        for dir_name in dirs_to_remove:
            if os.path.exists(dir_name):
                try:
                    shutil.rmtree(dir_name)
                    print(f"   Removed directory: {dir_name}")
                except Exception as e:
                    print(f"   Failed to remove directory {dir_name}: {e}")
                    success = False

        import glob
        for pattern in files_to_remove:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    print(f"   Removed file: {file_path}")
                except Exception as e:
                    print(f"   Failed to remove file {file_path}: {e}")
                    success = False

        return success

    def check_dependencies(self) -> bool:
        """필요한 종속성 확인"""
        print("Checking dependencies...")

        # PyInstaller 설치 여부 확인 (import 대신 명령어 실행)
        try:
            result = subprocess.run([sys.executable, "-m", "pyinstaller", "--version"], 
                                    capture_output=True, text=True, check=True)
            version = result.stdout.strip().split()[-1]  # 버전 추출
            print(f"   PyInstaller {version} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   PyInstaller is not installed.")
            if self._ask_install("PyInstaller"):
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
                    print("   PyInstaller installed successfully")
                except subprocess.CalledProcessError:
                    print("   Failed to install PyInstaller")
                    return False
            else:
                return False

        # 메인 스크립트 존재 확인
        if not os.path.exists(self.config.main_script):
            print(f"   Main script {self.config.main_script} not found.")
            return False

        print("   All dependencies checked")
        return True

    def build(self) -> bool:
        """실행 파일 빌드"""
        print("Starting CSV Analyzer build...")
        print("   (This process may take a few minutes...)")

        cmd = self.config.get_pyinstaller_args()

        try:
            print(f"   Executing command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("   Build process completed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   Build failed: {e}")
            if e.stderr:
                print(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            print(f"   Error during build: {e}")
            return False

    def check_result(self) -> bool:
        """빌드 결과 확인"""
        exe_name = f"{self.config.name}.exe" if self.config.is_windows else self.config.name
        exe_path = Path('dist') / exe_name

        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\nBuild successful!")
            print(f"Generated file: {exe_path}")
            print(f"File size: {size_mb:.1f} MB")

            # 실행 테스트 옵션
            if self._ask_run():
                self._run_executable(exe_path)

            return True
        else:
            print("   Executable was not created.")
            return False

    def _ask_install(self, package: str) -> bool:
        """패키지 설치 여부 확인"""
        try:
            # CI/CD 환경에서는 자동으로 설치
            if os.environ.get('CI') or not sys.stdin.isatty():
                print(f"Installing {package} automatically...")
                return True

            response = input(f"Do you want to install {package}? (y/n): ").strip().lower()
            return response in ['y', 'yes', '']
        except:
            return True  # 기본적으로 설치 시도

    def _ask_run(self) -> bool:
        """실행 파일 실행 여부 확인"""
        try:
            # CI/CD 환경에서는 실행하지 않음
            if os.environ.get('CI') or not sys.stdin.isatty():
                return False

            response = input("\nDo you want to test the built executable now? (y/n): ").strip().lower()
            return response in ['y', 'yes', '']
        except:
            return False

    def _run_executable(self, exe_path: Path):
        """실행 파일 실행"""
        try:
            if self.config.is_windows:
                os.startfile(str(exe_path))
            else:
                subprocess.run(['xdg-open' if self.config.is_linux else 'open', str(exe_path)])
            print("   Executable launched")
        except Exception as e:
            print(f"   Failed to launch executable: {e}")

def main():
    """메인 함수"""
    print("=" * 60)
    print("CSV Analyzer Build Tool")
    print("=" * 60)

    # 명령줄 인자 처리
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['-h', '--help', 'help']:
            print(__doc__)
            return True
        elif arg in ['--clean', 'clean']:
            config = BuildConfig()
            builder = BuildTool(config)
            success = builder.cleanup()
            print("Cleanup complete!" if success else "Cleanup failed!")
            return success

    print("Starting build process...")
    print()

    # 빌드 설정 및 도구 초기화
    config = BuildConfig()
    builder = BuildTool(config)

    start_time = time.time()

    try:
        # 1. 정리
        if not builder.cleanup():
            print("Cleanup step failed")
            return False
        print()

        # 2. 종속성 확인
        if not builder.check_dependencies():
            print("Dependency check failed")
            return False
        print()

        # 3. 빌드
        if not builder.build():
            print("Build failed")
            return False
        print()

        # 4. 결과 확인
        if not builder.check_result():
            return False

        # 빌드 시간 출력
        end_time = time.time()
        build_time = end_time - start_time
        print(f"\nTotal build time: {build_time:.1f}s")

        return True

    except KeyboardInterrupt:
        print("\nAborted by user.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()

    if not success:
        print("\nBuild failed")
        if platform.system() == "Windows":
            input("Press Enter to exit...")
        sys.exit(1)
    else:
        print("\nBuild complete")
        if platform.system() == "Windows":
            input("Press Enter to exit...")
