#!/usr/bin/env python3
"""
CSV Analyzer 통합 빌드 스크립트
PyInstaller를 사용하여 크로스 플랫폼 실행 파일을 생성합니다.

사용법:
  python build.py              # 표준 빌드
  python build.py --optimized  # 최적화 빌드
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

    def __init__(self, mode: str = "standard"):
        self.mode = mode
        self.name = "CSV-Analyzer"
        self.main_script = "app.py"
        self.console = False
        self.onefile = True
        self.optimize = 2 if mode == "optimized" else 1

        # 플랫폼별 설정
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux"
        self.is_macos = platform.system() == "Darwin"

        # 제외할 모듈들
        self.exclude_modules = self._get_exclude_modules()

        # 추가 데이터 파일들
        self.datas = [
            ("README.md", "."),
            ("dsl_tokenizer.json", "."),
        ]

    def _get_exclude_modules(self) -> List[str]:
        """빌드 모드에 따른 제외 모듈 목록"""
        base_excludes = [
            'dearpygui',  # 사용하지 않는 GUI 라이브러리
            'PyQt5', 'PyQt6', 'PySide2', 'PySide6',  # Qt 라이브러리
            'wx',  # wxPython
            'tkinter',  # 표준 tkinter (dearpygui 사용)
            'test', 'unittest', 'pytest',  # 테스트 모듈들
            'IPython', 'jupyter', 'notebook',  # Jupyter 관련
        ]

        if self.mode == "optimized":
            # 최적화 모드에서 추가 제외
            optimized_excludes = [
                'torch', 'torchvision',  # PyTorch
                'tensorflow', 'keras',   # TensorFlow
                'sklearn',               # scikit-learn
                'scipy.spatial.distance', # scipy 일부
                'PIL.ImageQt',          # PIL Qt 지원
            ]
            base_excludes.extend(optimized_excludes)

        return base_excludes

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
        print("🧹 이전 빌드 파일 정리 중...")

        dirs_to_remove = ['build', 'dist', '__pycache__']
        files_to_remove = ['*.spec']

        success = True

        for dir_name in dirs_to_remove:
            if os.path.exists(dir_name):
                try:
                    shutil.rmtree(dir_name)
                    print(f"   ✓ {dir_name} 폴더 제거")
                except Exception as e:
                    print(f"   ❌ {dir_name} 폴더 제거 실패: {e}")
                    success = False

        import glob
        for pattern in files_to_remove:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    print(f"   ✓ {file_path} 파일 제거")
                except Exception as e:
                    print(f"   ❌ {file_path} 파일 제거 실패: {e}")
                    success = False

        return success

    def check_dependencies(self) -> bool:
        """필요한 종속성 확인"""
        print("🔍 종속성 확인 중...")

        try:
            import PyInstaller
            print(f"   ✓ PyInstaller {PyInstaller.__version__}")
        except ImportError:
            print("   ❌ PyInstaller가 설치되지 않았습니다.")
            if self._ask_install("PyInstaller"):
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
                    print("   ✓ PyInstaller 설치 완료")
                except subprocess.CalledProcessError:
                    print("   ❌ PyInstaller 설치 실패")
                    return False
            else:
                return False

        # 메인 스크립트 존재 확인
        if not os.path.exists(self.config.main_script):
            print(f"   ❌ 메인 스크립트 {self.config.main_script}를 찾을 수 없습니다.")
            return False

        print("   ✓ 모든 종속성 확인 완료")
        return True

    def build(self) -> bool:
        """실행 파일 빌드"""
        mode_name = "최적화" if self.config.mode == "optimized" else "표준"
        print(f"🔨 {mode_name} 모드로 CSV Analyzer 빌드 중...")
        print("   (이 과정은 수 분이 소요될 수 있습니다...)")

        cmd = self.config.get_pyinstaller_args()

        try:
            print(f"   실행 명령어: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("   ✅ 빌드 성공!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 빌드 실패: {e}")
            if e.stderr:
                print(f"   오류 출력: {e.stderr}")
            return False
        except Exception as e:
            print(f"   ❌ 빌드 중 오류 발생: {e}")
            return False

    def check_result(self) -> bool:
        """빌드 결과 확인"""
        exe_name = f"{self.config.name}.exe" if self.config.is_windows else self.config.name
        exe_path = Path('dist') / exe_name

        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n🎉 빌드 성공!")
            print(f"📁 생성된 파일: {exe_path}")
            print(f"📏 파일 크기: {size_mb:.1f} MB")

            # 실행 테스트 옵션
            if self._ask_run():
                self._run_executable(exe_path)

            return True
        else:
            print("❌ 실행 파일이 생성되지 않았습니다.")
            return False

    def _ask_install(self, package: str) -> bool:
        """패키지 설치 여부 확인"""
        try:
            # CI/CD 환경에서는 자동으로 설치
            if os.environ.get('CI') or not sys.stdin.isatty():
                print(f"   🔄 {package} 자동 설치 중...")
                return True

            response = input(f"{package}를 설치하시겠습니까? (y/n): ").strip().lower()
            return response in ['y', 'yes', '']
        except:
            return True  # 기본적으로 설치 시도

    def _ask_run(self) -> bool:
        """실행 파일 실행 여부 확인"""
        try:
            # CI/CD 환경에서는 실행하지 않음
            if os.environ.get('CI') or not sys.stdin.isatty():
                return False

            response = input("\n🚀 빌드된 실행 파일을 지금 테스트하시겠습니까? (y/n): ").strip().lower()
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
            print("   ✅ 실행 파일 실행됨")
        except Exception as e:
            print(f"   ❌ 실행 파일 실행 실패: {e}")

def main():
    """메인 함수"""
    print("=" * 60)
    print("       🔧 CSV Analyzer 빌드 도구 🔧")
    print("=" * 60)

    # 명령줄 인자 처리
    mode = "standard"  # 기본 모드

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['-h', '--help', 'help']:
            print(__doc__)
            return True
        elif arg in ['--clean', 'clean']:
            config = BuildConfig()
            builder = BuildTool(config)
            success = builder.cleanup()
            print("✅ 정리 완료!" if success else "❌ 정리 실패!")
            return success
        elif arg in ['--optimized', 'optimized', '-o']:
            mode = "optimized"
        elif arg in ['--standard', 'standard', '-s']:
            mode = "standard"
        else:
            print(f"❌ 알 수 없는 옵션: {sys.argv[1]}")
            print("\n사용법:")
            print("  python build.py              # 표준 빌드")
            print("  python build.py --optimized  # 최적화 빌드")
            print("  python build.py --clean      # 빌드 파일 정리")
            print("  python build.py --help       # 도움말")
            return False

    mode_name = "최적화" if mode == "optimized" else "표준"
    print(f"📦 {mode_name} 모드로 빌드 시작...")
    print()

    # 빌드 설정 및 도구 초기화
    config = BuildConfig(mode)
    builder = BuildTool(config)

    start_time = time.time()

    try:
        # 1. 정리
        if not builder.cleanup():
            print("❌ 정리 단계 실패")
            return False
        print()

        # 2. 종속성 확인
        if not builder.check_dependencies():
            print("❌ 종속성 확인 실패")
            return False
        print()

        # 3. 빌드
        if not builder.build():
            print("❌ 빌드 실패")
            return False
        print()

        # 4. 결과 확인
        if not builder.check_result():
            return False

        # 빌드 시간 출력
        end_time = time.time()
        build_time = end_time - start_time
        print(f"\n⏱️  총 빌드 시간: {build_time:.1f}초")

        return True

    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

if __name__ == "__main__":
    success = main()

    if not success:
        print("\n❌ 빌드 실패")
        if platform.system() == "Windows":
            input("엔터를 누르면 종료합니다...")
        sys.exit(1)
    else:
        print("\n✅ 빌드 완료")
        if platform.system() == "Windows":
            input("엔터를 누르면 종료합니다...")
