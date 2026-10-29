@echo off
setlocal
cd /d "%~dp0"
title Sheepper
echo.
echo === Sheepper ===
echo.

where node >nul 2>nul
if errorlevel 1 goto nonode

for /f %%v in ('node -p "process.versions.node.split('.')[0]"') do set NODE_MAJOR=%%v
if not defined NODE_MAJOR goto nonode
if %NODE_MAJOR% LSS 22 goto oldnode

if exist "node_modules" goto hasmodules
echo Prima volta: installo le dipendenze. Ci vuole qualche minuto...
call npm ci
if errorlevel 1 goto fail
:hasmodules

set REBUILD=0
if /i "%~1"=="--rebuild" set REBUILD=1
if not exist ".next\BUILD_ID" set REBUILD=1
if "%REBUILD%"=="0" goto hasbuild
echo Preparo l'app. Ci vuole un po'...
call npm run build
if errorlevel 1 goto fail
:hasbuild

echo.
echo Avvio Sheepper su http://127.0.0.1:3000
echo Il browser si apre da solo tra pochi secondi.
echo Per fermare Sheepper chiudi questa finestra.
echo.
if /i "%SHEEPPER_NO_BROWSER%"=="1" goto startserver
start "" /b cmd /c "ping -n 4 127.0.0.1 >nul & start "" http://127.0.0.1:3000"
:startserver
call npm run start
goto end

:nonode
echo ERRORE: Node.js non e' installato.
echo Scarica la versione 22 o piu' recente da https://nodejs.org
echo poi fai di nuovo doppio clic su questo file.
goto fail

:oldnode
echo ERRORE: la versione di Node.js (%NODE_MAJOR%) e' troppo vecchia.
echo Serve la versione 22 o piu' recente: scaricala da https://nodejs.org
echo poi fai di nuovo doppio clic su questo file.
goto fail

:fail
echo.
echo Qualcosa non ha funzionato. Leggi il messaggio qui sopra.
if not "%SHEEPPER_NO_PAUSE%"=="1" pause
exit /b 1

:end
endlocal
