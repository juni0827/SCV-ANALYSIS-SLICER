@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
echo ========================================
echo      CSV Analyzer 빌드 도구
echo ========================================
echo.

echo 빌드 옵션을 선택하세요:
echo 1. 기본 빌드 (전체 라이브러리 포함) - 약 5-10분 소요
echo 2. 최적화된 빌드 (불필요한 라이브러리 제외, 권장) - 약 2-3분 소요
echo.
set /p choice="선택 (1 또는 2): "

if "%choice%"=="2" (
    echo.
    echo 🚀 최적화된 빌드 실행 중...
    python build_optimized.py
    goto :end
)

echo.
echo 🧹 이전 빌드 파일 정리 중...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec
echo    ✓ 이전 빌드 파일 정리 완료
echo.

echo 🔨 CSV Analyzer 실행 파일 빌드 중...
echo    (이 과정은 5-10분이 소요될 수 있습니다...)
echo.

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name="CSV-Analyzer" ^
    --exclude-module=dearpygui ^
    --exclude-module=PyQt5 ^
    --exclude-module=PyQt6 ^
    --exclude-module=PySide2 ^
    --exclude-module=PySide6 ^
    --exclude-module=wx ^
    --add-data="README.md;." ^
    app.py

echo.
if exist dist\CSV-Analyzer.exe (
    echo ✅ 빌드 성공!
    echo    실행 파일: dist\CSV-Analyzer.exe
    for %%I in (dist\CSV-Analyzer.exe) do (
        set /a size_mb=%%~zI/1024/1024
        echo    파일 크기: %%~zI bytes (약 !size_mb! MB^)
    )
    echo.
    set /p run_choice="빌드된 실행 파일을 지금 실행하시겠습니까? (y/n): "
    if /i "!run_choice!"=="y" (
        start "" "dist\CSV-Analyzer.exe"
    )
) else (
    echo ❌ 빌드 실패!
    echo    오류 로그를 확인해주세요.
)

:end
echo.
echo 아무 키나 누르면 종료합니다...
pause >nul
