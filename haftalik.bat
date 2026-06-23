@echo off
rem Zamanlanmis gorev (Task Scheduler) bu dosyayi calistirir.
rem Ekran gostermez; ciktiyi son_calisma.log dosyasina yazar.
chcp 65001 >nul
cd /d "%~dp0"
echo ===== %date% %time% ===== >> son_calisma.log
"C:\Users\MevlutOz\AppData\Local\Programs\Python\Python312\python.exe" run.py >> son_calisma.log 2>&1
