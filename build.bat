@echo off
echo =====================================
echo       CSV Analyzer 빌드 스크립트
echo =====================================
echo.

echo 1. 기존 빌드 파일 정리...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

echo 2. PyInstaller로 실행 파일 생성 중...
echo    (이 과정은 몇 분이 소요될 수 있습니다...)
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

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =====================================
    echo       빌드 성공!
    echo =====================================
    echo.
    echo 생성된 파일: dist\CSV-Analyzer.exe
    echo 파일 크기:
    for %%I in (dist\CSV-Analyzer.exe) do echo    %%~zI bytes
    echo.
    echo 실행하려면 dist 폴더의 CSV-Analyzer.exe를 더블클릭하세요.
    echo.
    
    REM 실행 파일 자동으로 열기 (선택사항)
    set /p choice="빌드된 실행 파일을 지금 실행하시겠습니까? (y/n): "
    if /i "%choice%"=="y" (
        start "" "dist\CSV-Analyzer.exe"
    )
) else (
    echo.
    echo =====================================
    echo       빌드 실패!
    echo =====================================
    echo.
    echo 오류가 발생했습니다. 위의 오류 메시지를 확인하세요.
)

echo.
pause
