@echo off
setlocal
cd /d %~dp0

echo [DotVis Build Script]
echo Converting icon if necessary...
if not exist "assets\icon.ico" (
    if exist "assets\icon.png" (
        python -c "from PIL import Image; img = Image.open('assets/icon.png'); img.save('assets/icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])"
    ) else (
        echo Warning: assets\icon.png not found. Build will continue without custom icon.
    )
)

echo Starting Nuitka build...
python -m nuitka ^
    --standalone ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --windows-icon-from-ico=assets/icon.ico ^
    --include-data-file=appversion.toml=appversion.toml ^
    --include-data-dir=assets=assets ^
    --output-dir=dist ^
    --remove-output ^
    --output-filename=DotVis ^
    main.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo --------------------------------------------------
    echo Build completed successfully!
    echo Output: dist\main.dist\DotVis.exe
    echo --------------------------------------------------
) else (
    echo.
    echo --------------------------------------------------
    echo Build failed with error code %ERRORLEVEL%.
    echo --------------------------------------------------
)

pause
