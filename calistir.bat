@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   SaaS Bridge - Haftalik Instagram Agent
echo ============================================
echo.
"C:\Users\MevlutOz\AppData\Local\Programs\Python\Python312\python.exe" run.py
echo.
echo --------------------------------------------
echo  Bitti. Ciktilar: output\^<tarih^>\ klasorunde
echo  (captions.md + post_*.png)
echo --------------------------------------------
echo  Kapatmak icin bir tusa bas...
pause >nul
