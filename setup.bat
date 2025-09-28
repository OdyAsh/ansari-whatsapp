@echo off
REM Setup script for ansari-whatsapp service on Windows

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create empty .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file with your WhatsApp API credentials
)

REM Create logs directory
if not exist logs (
    mkdir logs
)

echo Setup complete. To run the service, use: python -m src.ansari_whatsapp.app.main