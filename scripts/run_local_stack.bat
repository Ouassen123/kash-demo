@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_local_stack.ps1"
exit /b %ERRORLEVEL%
