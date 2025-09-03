#!/usr/bin/env python3
"""
단일 인스턴스 관리 모듈
Windows 뮤텍스를 사용하여 애플리케이션의 중복 실행을 방지합니다.
"""

import os
import sys
import time
import threading
from pathlib import Path

# Windows API constants
PROCESS_QUERY_INFORMATION = 0x0400
ERROR_ALREADY_EXISTS = 183

# Timeout constants (in milliseconds)
WINDOW_OPERATION_TIMEOUT_MS = 100


class SingleInstanceManager:
    """단일 인스턴스 관리 클래스"""
    
    def __init__(self, app_name="CSV-Analyzer", show_message=True):
        self.app_name = app_name
        self.show_message = show_message
        self.mutex = None
        self.lock_file = None
        self.is_running = False
        self.main_window = None
        
    def is_another_instance_running(self):
        """다른 인스턴스가 실행 중인지 확인"""
        try:
            if sys.platform.startswith('win'):
                return self._check_windows_mutex()
            else:
                return self._check_lock_file()
        except Exception as e:
            print(f"Warning: Could not check for other instances: {e}")
            return False
    
    def _check_windows_mutex(self):
        """Windows 뮤텍스를 사용한 단일 인스턴스 체크"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Windows API 함수들
            kernel32 = ctypes.windll.kernel32
            
            # 뮤텍스 이름 (전역적으로 고유해야 함)
            mutex_name = f"Global\\{self.app_name}-SingleInstance-Mutex"
            
            # 뮤텍스 생성 또는 열기 시도
            self.mutex = kernel32.CreateMutexW(
                None,  # security attributes
                True,  # initial owner
                mutex_name  # mutex name
            )
            
            if not self.mutex:
                return False
                
            # 마지막 에러 코드 확인
            last_error = kernel32.GetLastError()
            
            # ERROR_ALREADY_EXISTS (183) = 이미 다른 인스턴스가 실행 중
            if last_error == ERROR_ALREADY_EXISTS:
                kernel32.CloseHandle(self.mutex)
                self.mutex = None
                return True
                
            return False
            
        except ImportError:
            # ctypes가 없거나 Windows가 아닌 경우 파일 락 사용
            return self._check_lock_file()
        except Exception as e:
            print(f"Mutex check failed: {e}")
            return self._check_lock_file()
    
    def _check_lock_file(self):
        """파일 락을 사용한 단일 인스턴스 체크 (크로스 플랫폼)"""
        try:
            # 임시 디렉토리에 락 파일 생성
            if sys.platform.startswith('win'):
                lock_dir = Path(os.environ.get('TEMP', '/tmp'))
            else:
                lock_dir = Path('/tmp')
                
            lock_dir.mkdir(exist_ok=True)
            self.lock_file = lock_dir / f"{self.app_name}.lock"
            
            # 락 파일이 이미 존재하는지 확인
            if self.lock_file.exists():
                try:
                    # 파일 내용 읽기 (PID 정보)
                    with open(self.lock_file, 'r') as f:
                        pid_str = f.read().strip()
                        if pid_str.isdigit():
                            pid = int(pid_str)
                            # 프로세스가 실제로 실행 중인지 확인
                            if self._is_process_running(pid):
                                return True
                            else:
                                # 죽은 프로세스의 락 파일 제거
                                self.lock_file.unlink()
                except (IOError, ValueError):
                    # 파일을 읽을 수 없거나 형식이 잘못된 경우 락 파일 제거
                    try:
                        self.lock_file.unlink()
                    except:
                        pass
            
            # 새 락 파일 생성
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
                
            return False
            
        except Exception as e:
            print(f"Lock file check failed: {e}")
            return False
    
    def _is_process_running(self, pid):
        """특정 PID의 프로세스가 실행 중인지 확인"""
        try:
            if sys.platform.startswith('win'):
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                # Unix/Linux 시스템
                os.kill(pid, 0)  # 시그널 0으로 프로세스 존재 확인
                return True
        except (OSError, ImportError):
            return False
    
    def register_main_window(self, window):
        """메인 윈도우 등록 (다른 인스턴스에서 창을 앞으로 가져오기 위해)"""
        self.main_window = window
        
    def bring_to_front(self):
        """기존 인스턴스의 창을 앞으로 가져오기"""
        if not self.main_window:
            return False
            
        try:
            # Step 1: Check if window is minimized and restore if needed
            try:
                if self.main_window.state() == 'iconic':
                    self.main_window.deiconify()
                    # Small delay to allow window restoration
                    time.sleep(0.05)
            except Exception as e:
                print(f"Failed to deiconify window: {e}")
                # Continue with other operations even if deiconify fails
            
            # Step 2: Lift window to front
            try:
                self.main_window.lift()
            except Exception as e:
                print(f"Failed to lift window: {e}")
                return False
            
            # Step 3: Force focus
            try:
                self.main_window.focus_force()
            except Exception as e:
                print(f"Failed to force focus: {e}")
                # Continue even if focus fails
            
            # Step 4: Temporarily set topmost to ensure visibility
            try:
                self.main_window.attributes('-topmost', True)
                # Use the timeout constant for consistent timing
                self.main_window.after(WINDOW_OPERATION_TIMEOUT_MS, 
                                     lambda: self._remove_topmost_safely())
            except Exception as e:
                print(f"Failed to set topmost attribute: {e}")
                # Continue without topmost if it fails
            
            return True
        except Exception as e:
            print(f"Failed to bring window to front: {e}")
            return False
    
    def _remove_topmost_safely(self):
        """Safely remove topmost attribute with error handling"""
        try:
            if self.main_window:
                self.main_window.attributes('-topmost', False)
        except Exception as e:
            print(f"Failed to remove topmost attribute: {e}")
    
    def show_already_running_message(self):
        """이미 실행 중이라는 메시지 표시"""
        if not self.show_message:
            return
            
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            # 임시 루트 윈도우 생성 (메시지박스를 위해)
            temp_root = tk.Tk()
            temp_root.withdraw()  # 윈도우 숨기기
            
            messagebox.showinfo(
                "CSV Analyzer",
                f"{self.app_name}이 이미 실행 중입니다.\n"
                "기존 창을 확인해주세요."
            )
            
            temp_root.destroy()
            
        except Exception as e:
            print(f"Could not show message: {e}")
            print(f"{self.app_name} is already running.")
    
    def cleanup(self):
        """리소스 정리"""
        try:
            # Windows 뮤텍스 정리
            if self.mutex and sys.platform.startswith('win'):
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.CloseHandle(self.mutex)
                self.mutex = None
            
            # 락 파일 정리
            if self.lock_file and self.lock_file.exists():
                self.lock_file.unlink()
                
        except Exception as e:
            print(f"Cleanup failed: {e}")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.cleanup()


def check_single_instance(app_name="CSV-Analyzer", show_message=True):
    """
    단일 인스턴스 체크를 위한 편의 함수
    
    Returns:
        SingleInstanceManager: 인스턴스가 유일한 경우
        None: 이미 다른 인스턴스가 실행 중인 경우
    """
    manager = SingleInstanceManager(app_name, show_message)
    
    if manager.is_another_instance_running():
        manager.show_already_running_message()
        return None
    
    return manager


if __name__ == "__main__":
    # 테스트 코드
    print("단일 인스턴스 테스트...")
    
    manager = check_single_instance("CSV-Analyzer-Test")
    if manager:
        print("이 인스턴스가 첫 번째입니다.")
        print("5초 동안 대기... (이 시간 동안 다른 인스턴스를 실행해보세요)")
        time.sleep(5)
        manager.cleanup()
    else:
        print("다른 인스턴스가 이미 실행 중입니다.")