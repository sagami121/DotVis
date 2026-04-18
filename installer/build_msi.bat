@echo off
setlocal
cd /d %~dp0

echo [DotVis MSI Build Script]

echo Generating unique payload folder...
set "PAYLOAD_DIR=payload_%RANDOM%"
if exist "%PAYLOAD_DIR%" rd /s /q "%PAYLOAD_DIR%"
mkdir "%PAYLOAD_DIR%"

echo Preparing payload in %PAYLOAD_DIR%...
xcopy /e /y ..\dist\main.dist "%PAYLOAD_DIR%\" >nul
if exist "%PAYLOAD_DIR%\DotVis.exe" del /f /q "%PAYLOAD_DIR%\DotVis.exe"

echo Extracting version from appversion.toml...
for /f "tokens=2 delims==" %%i in ('findstr "version" ..\appversion.toml') do set APP_VERSION=%%i
set APP_VERSION=%APP_VERSION: =%
set APP_VERSION=%APP_VERSION:"=%

:: MSI version must be strictly numeric (Major.Minor.Build.Revision) or specific SemVer
:: Here we normalize it by replacing anything not a digit or dot with a dot, then cleaning up
for /f %%v in ('powershell -Command "$v = '%APP_VERSION%' -replace '[^0-9.]', '.0'; $v = $v.Trim('.'); while ($v.Split('.').Count -lt 3) { $v += '.0' }; $parts = $v.Split('.'); $parts[0..([Math]::Min($parts.Count, 3)-1)] -join '.'"') do set MSI_VERSION=%%v

echo Building MSI with WiX v4+ (ja-JP) for version %APP_VERSION% (MSI Version: %MSI_VERSION%)...
wix build ^
    -ext WixToolset.UI.wixext ^
    -culture ja-JP ^
    -out ..\dist\DotVis_%APP_VERSION%_x64_ja-JP.msi ^
    -d PayloadDir="%PAYLOAD_DIR%" ^
    -d AppVersion="%MSI_VERSION%" ^
    Package.wxs

echo Cleaning up %PAYLOAD_DIR%...
:: Try cleaning up with retries in case files are locked
set RETRY_COUNT=0
:cleanup_retry
rd /s /q "%PAYLOAD_DIR%" 2>nul
if exist "%PAYLOAD_DIR%" (
    set /a RETRY_COUNT+=1
    if %RETRY_COUNT% leq 5 (
        echo Cleanup failed, retrying in 2 seconds... (%RETRY_COUNT%/5)
        timeout /t 2 /nobreak >nul
        goto cleanup_retry
    ) else (
        echo Warning: Could not fully clean up %PAYLOAD_DIR%. Some files may be locked.
    )
)
if exist FilesFragment.wxs del FilesFragment.wxs

if %ERRORLEVEL% equ 0 (
    echo.
    echo --------------------------------------------------
    echo MSI build completed successfully!
    echo Output: dist\DotVis_%APP_VERSION%_x64_ja-JP.msi
    echo --------------------------------------------------
) else (
    echo.
    echo --------------------------------------------------
    echo MSI build failed with error code %ERRORLEVEL%.
    echo --------------------------------------------------
)

pause
