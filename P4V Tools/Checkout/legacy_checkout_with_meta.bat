@echo off
setlocal enabledelayedexpansion

REM ======================
REM Main loop: iterate all arguments from P4V (%*)
REM ======================
:main_loop
if "%~1"=="" goto done
call :checkout_file "%~1"
shift
goto main_loop

REM Function to checkout file + meta
:checkout_file
set "FILE=%~1"
if exist "!FILE!" (
    REM Check if the path contains Chinese characters
    set "HAS_CHINESE=0"
    for /f %%C in ('powershell -NoProfile -Command "Write-Output ([regex]::IsMatch('%FILE%','[\u4e00-\u9fff]'))"') do set "HAS_CHINESE=%%C"

    REM If there are Chinese characters, use -Q cp936 to checkout
    if "!HAS_CHINESE!"=="True" (
        p4 -Q cp936 edit "!FILE!"
    ) else (
        p4 edit "!FILE!"
    )

    REM Check if this is a folder (last 4 chars are \...)
    if /i "!FILE:~-4!"=="\..." (
        set "FILE=!FILE:~0,-4!"
    )

    REM Checkout corresponding .meta file if exists
    if exist "!FILE!.meta" (
        if "!HAS_CHINESE!"=="True" (
            p4 -Q cp936 edit "!FILE!.meta"
        ) else (
            p4 edit "!FILE!.meta"
        )
    )
)
goto :eof

:done
echo Done.