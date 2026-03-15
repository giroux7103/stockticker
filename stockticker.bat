@echo off

REM This batch file is used to start the stock ticker application.

SET CURDIR=%CD%

SET STHOME=%~dp0
SET ST_USE_HTTPS=%ST_USE_HTTPS%
IF "%ST_USE_HTTPS%"=="" SET ST_USE_HTTPS=1

SET ST_PUBLIC_HOST=%ST_PUBLIC_HOST%
IF "%ST_PUBLIC_HOST%"=="" SET ST_PUBLIC_HOST=localhost

SET BACKEND_PORT=%BACKEND_PORT%
IF "%BACKEND_PORT%"=="" SET BACKEND_PORT=8000

SET FRONTEND_PORT=%FRONTEND_PORT%
IF "%FRONTEND_PORT%"=="" SET FRONTEND_PORT=5173

IF "%ST_USE_HTTPS%"=="1" (
    SET BACKEND_SCHEME=https
    SET FRONTEND_SCHEME=https
) ELSE (
    SET BACKEND_SCHEME=http
    SET FRONTEND_SCHEME=http
)

SET CORS_ALLOWED_ORIGINS=%FRONTEND_SCHEME%://localhost:%FRONTEND_PORT%,%FRONTEND_SCHEME%://127.0.0.1:%FRONTEND_PORT%,%FRONTEND_SCHEME%://%ST_PUBLIC_HOST%:%FRONTEND_PORT%
SET VITE_API_BASE=%BACKEND_SCHEME%://%ST_PUBLIC_HOST%:%BACKEND_PORT%
SET VITE_DEV_PORT=%FRONTEND_PORT%

CD /D %STHOME%\backend

if not exist .venv (
    python -m venv .venv
    .\.venv\Scripts\python -m pip install -e .
)

call .\.venv\Scripts\activate.bat
IF "%ST_USE_HTTPS%"=="1" (
    IF "%BACKEND_SSL_CERT_FILE%"=="" (
        ECHO BACKEND_SSL_CERT_FILE is required when ST_USE_HTTPS=1
        GOTO :done
    )
    IF "%BACKEND_SSL_KEY_FILE%"=="" (
        ECHO BACKEND_SSL_KEY_FILE is required when ST_USE_HTTPS=1
        GOTO :done
    )
    start "Backend" uvicorn app.main:app --reload --host 0.0.0.0 --port %BACKEND_PORT% --ssl-certfile "%BACKEND_SSL_CERT_FILE%" --ssl-keyfile "%BACKEND_SSL_KEY_FILE%"
) ELSE (
    start "Backend" uvicorn app.main:app --reload --host 0.0.0.0 --port %BACKEND_PORT%
)
call .\.venv\Scripts\deactivate.bat

CD /D %STHOME%\frontend
REM npm install
IF "%ST_USE_HTTPS%"=="1" (
    IF "%FRONTEND_SSL_CERT_FILE%"=="" (
        ECHO FRONTEND_SSL_CERT_FILE is required when ST_USE_HTTPS=1
        GOTO :done
    )
    IF "%FRONTEND_SSL_KEY_FILE%"=="" (
        ECHO FRONTEND_SSL_KEY_FILE is required when ST_USE_HTTPS=1
        GOTO :done
    )
    SET VITE_DEV_HTTPS=true
    SET VITE_DEV_SSL_CERT_FILE=%FRONTEND_SSL_CERT_FILE%
    SET VITE_DEV_SSL_KEY_FILE=%FRONTEND_SSL_KEY_FILE%
) ELSE (
    SET VITE_DEV_HTTPS=false
)

start "Frontend" npm run dev

:done
CD /D %CURDIR%
