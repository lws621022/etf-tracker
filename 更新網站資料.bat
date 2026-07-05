@echo off
python scripts/update_data.py
if errorlevel 1 (
  echo.
  echo 資料更新失敗，請查看上方錯誤訊息。
  pause
  exit /b %errorlevel%
)
echo.
echo 更新完成。
pause
