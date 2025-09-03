@echo off
echo =====================================
echo    CSV Analyzer 단일 인스턴스 빌드
echo =====================================
echo.

echo 1. 기존 빌드 파일 정리...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

echo 2. 단일 인스턴스 기능 테스트...
python test_single_instance.py
if %ERRORLEVEL% NEQ 0 (
    echo    ❌ 단일 인스턴스 테스트 실패!
    echo    빌드를 중단합니다.
    goto :error
)
echo    ✅ 단일 인스턴스 테스트 통과

echo.
echo 3. PyInstaller로 실행 파일 생성 중...
echo    (이 과정은 몇 분이 소요될 수 있습니다...)
echo.

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name="CSV-Analyzer" ^
    --clean ^
    --optimize=2 ^
    --exclude-module=dearpygui ^
    --exclude-module=PyQt5 ^
    --exclude-module=PyQt6 ^
    --exclude-module=PySide2 ^
    --exclude-module=PySide6 ^
    --exclude-module=wx ^
    --exclude-module=test ^
    --exclude-module=unittest ^
    --add-data="README.md;." ^
    --hidden-import=single_instance ^
    --hidden-import=ctypes ^
    --hidden-import=ctypes.wintypes ^
    app.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =====================================
    echo       빌드 성공!
    echo =====================================
    echo.
    echo 생성된 파일: dist\CSV-Analyzer.exe
    
    if exist "dist\CSV-Analyzer.exe" (
        echo 파일 크기:
        for %%I in (dist\CSV-Analyzer.exe) do echo    %%~zI bytes (%%~zI ÷ 1024 ÷ 1024 MB)
        echo.
        echo ✅ 단일 인스턴스 기능이 포함된 실행 파일이 생성되었습니다.
        echo 📌 EXE를 여러 번 실행해도 하나의 창만 열립니다.
        echo.
        
        REM 실행 파일 자동으로 열기 (선택사항)
        set /p choice="빌드된 실행 파일을 지금 실행하시겠습니까? (y/n): "
        if /i "%choice%"=="y" (
            echo 실행 중... (단일 인스턴스 테스트를 위해 여러 번 더블클릭해보세요)
            start "" "dist\CSV-Analyzer.exe"
        )
    ) else (
        goto :error
    )
) else (
    goto :error
)

echo.
echo =====================================
echo       빌드 완료!
echo =====================================
pause
exit /b 0

:error
echo.
echo =====================================
echo       빌드 실패!
echo =====================================
echo.
echo 오류가 발생했습니다. 위의 오류 메시지를 확인하세요.
echo.
pause
exit /b 1
