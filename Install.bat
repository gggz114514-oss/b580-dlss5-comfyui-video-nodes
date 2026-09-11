@echo off
chcp 65001 >nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
  echo Installation failed. Keep the error message above.
  pause
  exit /b 1
)
echo Installation completed. Restart ComfyUI to use NR B580 nodes.
pause
