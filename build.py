#!/usr/bin/env python3
"""
CSV Analyzer integrated build script
Generates cross-platform executables using PyInstaller.

Usage:
  python build.py              # Start build
  python build.py --clean      # Clean build files only
  python build.py --help       # Show help
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
    """Build configuration class"""

    def __init__(self):
        self.name = "CSV-Analyzer"
        self.main_script = "src/gui/app.py"
        self.console = False
        self.onefile = True
        self.optimize = 1  # Default optimization level

        # Platform-specific configuration
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux"
        self.is_macos = platform.system() == "Darwin"

        # Modules to exclude
        self.exclude_modules = self._get_exclude_modules()

        # Additional data files
        self.datas = [
            ("README.md", "."),
            ("src/dsl/dsl_tokenizer.json", "src/dsl"),
            ("src/dsl/model.pt", "src/dsl"),
        ]

    def _get_exclude_modules(self) -> List[str]:
        """List of modules to exclude"""
        return [
            "dearpygui",  # Unused GUI library
            "PyQt5",
            "PyQt6",
            "PySide2",
            "PySide6",  # Qt libraries
            "wx",  # wxPython
            "tkinter",  # Standard tkinter (using dearpygui)
            "test",
            "unittest",
            "pytest",  # Test modules
            "IPython",
            "jupyter",
            "notebook",  # Jupyter-related
        ]

    def get_pyinstaller_args(self) -> List[str]:
        """Generate PyInstaller command arguments"""
        args = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--name",
            self.name,
            "--optimize",
            str(self.optimize),
        ]

        if self.onefile:
            args.append("--onefile")

        if not self.console:
            args.append("--windowed")

        # Add excluded modules
        for module in self.exclude_modules:
            args.extend(["--exclude-module", module])

        # Additional data files
        for src, dst in self.datas:
            if os.path.exists(src):
                # Platform-specific path separator
                separator = ":" if not self.is_windows else ";"
                args.extend(["--add-data", f"{src}{separator}{dst}"])

        # Main script
        args.append(self.main_script)

        return args


class BuildTool:
    """Build tool class"""

    def __init__(self, config: BuildConfig):
        self.config = config

    def cleanup(self) -> bool:
        """Clean up previous build files"""
        print("Cleaning up previous build files...")

        dirs_to_remove = ["build", "dist", "__pycache__"]
        files_to_remove = ["*.spec"]

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
        """Check required dependencies"""
        print("Checking dependencies...")

        # Check if PyInstaller is installed (run command instead of import)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pyinstaller", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            version = result.stdout.strip().split()[-1]  # Extract version
            print(f"   PyInstaller {version} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   PyInstaller is not installed.")
            if self._ask_install("PyInstaller"):
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "pyinstaller"],
                        check=True,
                    )
                    print("   PyInstaller installed successfully")
                except subprocess.CalledProcessError:
                    print("   Failed to install PyInstaller")
                    return False
            else:
                return False

        # Check main script exists
        if not os.path.exists(self.config.main_script):
            print(f"   Main script {self.config.main_script} not found.")
            return False

        print("   All dependencies checked")
        return True

    def build(self) -> bool:
        """Build executable file"""
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
        """Check build result"""
        exe_name = (
            f"{self.config.name}.exe" if self.config.is_windows else self.config.name
        )
        exe_path = Path("dist") / exe_name

        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\nBuild successful!")
            print(f"Generated file: {exe_path}")
            print(f"File size: {size_mb:.1f} MB")

            # Test execution option
            if self._ask_run():
                self._run_executable(exe_path)

            return True
        else:
            print("   Executable was not created.")
            return False

    def _ask_install(self, package: str) -> bool:
        """Ask whether to install package"""
        try:
            # Automatically install in CI/CD environment
            if os.environ.get("CI") or not sys.stdin.isatty():
                print(f"Installing {package} automatically...")
                return True

            response = (
                input(f"Do you want to install {package}? (y/n): ").strip().lower()
            )
            return response in ["y", "yes", ""]
        except:
            return True  # Attempt installation by default

    def _ask_run(self) -> bool:
        """Ask whether to run executable"""
        try:
            # Don't run in CI/CD environment
            if os.environ.get("CI") or not sys.stdin.isatty():
                return False

            response = (
                input("\nDo you want to test the built executable now? (y/n): ")
                .strip()
                .lower()
            )
            return response in ["y", "yes", ""]
        except:
            return False

    def _run_executable(self, exe_path: Path):
        """Run executable file"""
        try:
            if self.config.is_windows:
                os.startfile(str(exe_path))
            else:
                subprocess.run(
                    ["xdg-open" if self.config.is_linux else "open", str(exe_path)]
                )
            print("   Executable launched")
        except Exception as e:
            print(f"   Failed to launch executable: {e}")


def main():
    """Main function"""
    print("=" * 60)
    print("CSV Analyzer Build Tool")
    print("=" * 60)

    # Process command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["-h", "--help", "help"]:
            print(__doc__)
            return True
        elif arg in ["--clean", "clean"]:
            config = BuildConfig()
            builder = BuildTool(config)
            success = builder.cleanup()
            print("Cleanup complete!" if success else "Cleanup failed!")
            return success

    print("Starting build process...")
    print()

    # Initialize build configuration and tool
    config = BuildConfig()
    builder = BuildTool(config)

    start_time = time.time()

    try:
        # 1. Cleanup
        if not builder.cleanup():
            print("Cleanup step failed")
            return False
        print()

        # 2. Check dependencies
        if not builder.check_dependencies():
            print("Dependency check failed")
            return False
        print()

        # 3. Build
        if not builder.build():
            print("Build failed")
            return False
        print()

        # 4. Check result
        if not builder.check_result():
            return False

        # Print build time
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
