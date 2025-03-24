@echo off
REM Automate Odoo Deployment to Google Cloud Run

REM Load environment variables from .env file
echo Loading environment variables from .env...
for /f "tokens=1,2 delims==" %%a in (.env) do (
    set %%a=%%b
)

REM 1. Authenticate with Google Cloud (if needed)
echo Authenticating with Google Cloud...
@REM gcloud auth configure-docker

REM 2. Build the Docker image for Cloud Run
echo Building the Docker image...
docker build --platform=linux/amd64 -t %IMAGE_NAME% .

REM 3. Push the Docker image to Google Artifact Registry
echo Pushing the Docker image to Google Cloud...
docker push %IMAGE_NAME%

REM 4. Deploy Odoo to Google Cloud Run
echo Deploying Odoo to Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
    --image=%IMAGE_NAME% ^
    --platform=managed ^
    --region=%REGION% ^
    --allow-unauthenticated ^
    --port %PORT% ^
    --add-cloudsql-instances=%CLOUDSQL_INSTANCE% ^
    --set-env-vars="DB_HOST=%DB_HOST%,DB_USER=%DB_USER%,DB_PASSWORD=%DB_PASSWORD%,DATA_DIR=%DATA_DIR%" ^
    --service-account=%SERVICE_ACCOUNT%

REM 5. Get Cloud Run Service URL
echo Fetching Cloud Run Service URL...
FOR /F "tokens=*" %%g IN ('gcloud run services describe %SERVICE_NAME% --region=%REGION% --format "value(status.url)"') DO (SET SERVICE_URL=%%g)

REM 6. Display the Cloud Run URL
echo Odoo is deployed! Access it here: %SERVICE_URL%