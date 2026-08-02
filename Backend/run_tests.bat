@echo off
REM SocietyEase - API test runner (wrapper).
REM Double-click this, or run it from cmd.exe, if you would rather not deal
REM with PowerShell's execution policy. It just calls run_tests.ps1.
REM
REM   run_tests.bat              run everything
REM   run_tests.bat -Detailed    show every individual test name
REM   run_tests.bat -Report      also regenerate docs\TEST_CASES.md

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_tests.ps1" %*
echo.
pause
