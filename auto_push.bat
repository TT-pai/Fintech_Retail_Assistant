@echo off
REM 自动推送到GitHub脚本
set msg=%1
if "%msg%"=="" set msg=auto commit

git add .
git commit -m "%msg%"
git push origin main

echo 推送完成，按任意键退出
pause