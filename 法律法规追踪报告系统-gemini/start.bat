@echo off
title 智能法律法规追踪系统 启动器

echo.
echo =====================================================
echo      正在启动 智能法律法规追踪系统 v2.0
echo =====================================================
echo.

REM 切换到批处理文件所在的目录，这样无论从哪里启动，路径都是正确的。
cd /d "%~dp0"

echo 当前项目目录: %cd%

REM 使用 pythonw.exe 启动GUI应用，可以避免在后台显示一个黑色的命令行窗口。
REM 如果您的环境中没有 pythonw.exe 或路径不通，可以将其改为 python.exe
echo 即将执行: pythonw .\src\main.py
echo.

pythonw .\src\main.py

echo.
echo ----------------------------------------
echo 应用已关闭。按任意键退出此窗口...
pause >nul
