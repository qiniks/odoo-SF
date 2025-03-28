@echo off
setlocal EnableDelayedExpansion

REM Load environment variables from the .env file and remove quotes
for /f "tokens=1,* delims==" %%a in (".env") do (
    set %%a=%%b
    set %%a=!%%a:"=!
)

REM Echo variables to debug
echo CLOUD_SQL_PROXY_PATH=%CLOUD_SQL_PROXY_PATH%
echo CREDENTIALS_PATH=%CREDENTIALS_PATH%
echo CLOUDSQL_INSTANCE=%CLOUDSQL_INSTANCE%

REM Set additional variables
SET ODOO_CONTAINER_NAME=odoo
SET ODOO_IMAGE_NAME=odoo:18.0
SET DB_HOST=host.docker.internal
SET DB_PORT=5432
SET DB_USER=odoo
SET DB_PASSWORD=odoo
SET DB_NAME=odoo

REM Check if Cloud SQL Proxy is already running
tasklist | findstr /I "cloud-sql-proxy.exe" >nul
IF %ERRORLEVEL% NEQ 0 (
    echo Cloud SQL Proxy is NOT running. Starting in a new Command Prompt...

    REM Use the full path to cloud-sql-proxy.exe without quotes
    start cmd /k ""C:\Program Files\cloud-sql-proxy.exe" --credentials-file="%CREDENTIALS_PATH%" %CLOUDSQL_INSTANCE%"
) ELSE (
    echo Cloud SQL Proxy is already running.
)

REM Wait for Cloud SQL Proxy to initialize
timeout /t 5

REM Stop and remove any running Odoo container
docker ps -q -f name=%ODOO_CONTAINER_NAME% >nul 2>nul
IF NOT ERRORLEVEL 1 (
    echo Stopping the running '%ODOO_CONTAINER_NAME%' container...
    docker stop %ODOO_CONTAINER_NAME%
    docker rm %ODOO_CONTAINER_NAME%
)

REM Build the Odoo Docker image
echo Building the Odoo Docker image...
docker build -t %ODOO_IMAGE_NAME% . 
IF ERRORLEVEL 1 (
    echo Docker build failed. Exiting.
    exit /b 1
)

echo Docker image built successfully.

REM Run the Odoo container
echo Running the Odoo container...
docker run -d --name %ODOO_CONTAINER_NAME% -p 8080:8080 -v odoo-data:/var/lib/odoo -v "%CD%/addons":/mnt/extra-addons -e DB_HOST=%DB_HOST% -e DB_PORT=%DB_PORT% -e DB_USER=%DB_USER% -e DB_PASSWORD=%DB_PASSWORD% -e DB_NAME=%DB_NAME% %ODOO_IMAGE_NAME%

REM Opening Odoo in the browser
echo Opening http://localhost:8080 in the browser...
start http://localhost:8080
