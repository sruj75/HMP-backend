#!/bin/bash

# Startup script for Render deployment
# This script pre-downloads AI models and then starts the token server

echo "🚀 Starting HMP Backend Services..."

# Pre-download AI models to avoid delays during first user connection
echo "📦 Pre-downloading AI models..."
python voiceagent.py download-files

# Check if model download was successful
if [ $? -eq 0 ]; then
    echo "✅ AI models downloaded successfully"
else
    echo "⚠️ Model download had issues, but continuing with startup"
fi

# Start the token server
echo "🌐 Starting token server..."
exec uvicorn token_server:app --host 0.0.0.0 --port $PORT
