@echo off

REM Load environment variables from the .env file
for /f "tokens=1,* delims==" %%a in (".env") do set %%a=%%b

REM Echo the environment variables to verify they are being loaded correctly
echo CLOUD_SQL_PROXY_PATH=%CLOUD_SQL_PROXY_PATH%
echo CREDENTIALS_PATH=%CREDENTIALS_PATH%
echo CLOUDSQL_INSTANCE=%CLOUDSQL_INSTANCE%

REM Set variables
SET ODOO_CONTAINER_NAME=odoo
SET ODOO_IMAGE_NAME=odoo:18.0
SET DB_HOST=host.docker.internal
SET DB_PORT=5432
SET DB_USER=odoo
SET DB_PASSWORD=odoo
SET DB_NAME=odoo

REM Stop and remove any running Odoo container
docker ps -q -f name=%ODOO_CONTAINER_NAME% >nul 2>nul
IF NOT ERRORLEVEL 1 (
    echo Stopping the running '%ODOO_CONTAINER_NAME%' container...
    docker stop %ODOO_CONTAINER_NAME%
    docker rm %ODOO_CONTAINER_NAME%
)

REM Ensure the Cloud SQL Proxy path is correct and start the Cloud SQL Proxy
echo Starting Cloud SQL Proxy...
start /B "" "%CLOUD_SQL_PROXY_PATH%" -credential-file="%CREDENTIALS_PATH%" %CLOUDSQL_INSTANCE%

REM Wait for the Cloud SQL Proxy to initialize
timeout /t 5

REM Build the Odoo Docker image (if not already built)
echo Building the Odoo Docker image...
docker build -t %ODOO_IMAGE_NAME% .
IF ERRORLEVEL 1 (
    echo Docker build failed. Exiting.
    exit /b 1
)

echo Docker image built successfully.

REM Run the Odoo container
echo Running the Odoo container...
docker run -d ^
    --name %ODOO_CONTAINER_NAME% ^
    -p 8080:8080 ^
    -v odoo-data:/var/lib/odoo ^
    -v "%CD%/addons":/mnt/extra-addons ^
    -e DB_HOST=%DB_HOST% ^
    -e DB_PORT=%DB_PORT% ^
    -e DB_USER=%DB_USER% ^
    -e DB_PASSWORD=%DB_PASSWORD% ^
    -e DB_NAME=%DB_NAME% ^
    %ODOO_IMAGE_NAME%

REM Opening Odoo in the browser
echo Opening http://localhost:8080 in the browser...
start http://localhost:8080
