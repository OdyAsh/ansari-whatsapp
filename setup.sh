#!/bin/bash
# Setup script for ansari-whatsapp service

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    echo "Activating virtual environment..."
    source venv/Scripts/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create empty .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your WhatsApp API credentials"
fi

# Create logs directory
mkdir -p logs

echo "Setup complete. To run the service, use: python -m src.ansari_whatsapp.app.main"