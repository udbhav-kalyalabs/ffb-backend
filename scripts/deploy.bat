@echo off
REM Build, push, and redeploy AgriAI to ECS (ap-south-1)

setlocal enabledelayedexpansion

set REGION=ap-south-1
set REPO=730335617294.dkr.ecr.ap-south-1.amazonaws.com/agriai-api
set IMAGE=agriai-api:latest
set CLUSTER=agriai-cluster
set SERVICE=agriai-service

REM Optional: override tag via TAG env (defaults to latest)
if "%TAG%"=="" set TAG=latest

echo Using tag: %TAG%

echo [1/4] Building image %IMAGE% (no-cache)...
docker build --no-cache -t %IMAGE% ..
if errorlevel 1 exit /b 1

echo [2/4] Logging in to ECR %REGION% ...
aws ecr get-login-password --region %REGION% | docker login --username AWS --password-stdin 730335617294.dkr.ecr.%REGION%.amazonaws.com
if errorlevel 1 exit /b 1

echo [3/4] Tagging and pushing to %REPO%:%TAG% ...
docker tag %IMAGE% %REPO%:%TAG%
docker push %REPO%:%TAG%
if errorlevel 1 exit /b 1

echo [4/4] Forcing new deployment on ECS service %SERVICE% ...
aws ecs update-service --cluster %CLUSTER% --service %SERVICE% --force-new-deployment --region %REGION%
if errorlevel 1 exit /b 1

echo Done. The service will pull the latest image and roll out shortly.
endlocal
