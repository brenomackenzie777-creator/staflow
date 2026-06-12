@echo off
echo ================================================
echo   StaFlow Deploy -- npx vercel --prod
echo ================================================
cd /d "%~dp0"
npx vercel --prod
pause
