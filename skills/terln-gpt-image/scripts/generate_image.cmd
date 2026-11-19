@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0generate_image.ps1" %*
exit /b %ERRORLEVEL%
