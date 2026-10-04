@echo off
echo ===================================================
echo   Pushing Walpar OCR Platform to GitHub for Render
echo ===================================================
echo.
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Code successfully pushed to GitHub!
    echo Now go to https://dashboard.render.com to deploy.
) else (
    echo [NOTE] If you haven't created the repository yet:
    echo 1. Open https://github.com/new
    echo 2. Repository name: walpar-ocr
    echo 3. Click "Create repository"
    echo 4. Then run this script again!
)
pause
