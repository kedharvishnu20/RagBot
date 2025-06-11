@echo off
echo Cleaning up RAG AI App project...

REM Remove Python cache directories
echo Removing Python cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

REM Remove compiled Python files
echo Removing .pyc files...
del /s /q *.pyc 2>nul

REM Remove temporary files
echo Removing temporary files...
del /s /q *.tmp 2>nul
del /s /q *.temp 2>nul
del /s /q *~ 2>nul

REM Remove log files (optional)
echo Removing log files...
del /s /q *.log 2>nul

REM Remove test files in study_docs
echo Removing test files...
del /q study_docs\test_*.txt 2>nul
del /q study_docs\test_*.py 2>nul

REM Remove backup database files
echo Removing backup database files...
del /q *.db.backup 2>nul
del /q *.db.old 2>nul

echo Cleanup complete!
pause
