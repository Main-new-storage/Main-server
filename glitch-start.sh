#!/bin/bash
set -e

echo "Starting Backdoor AI Learning Server on Glitch.com..."

# Set up Glitch-specific environment
echo "Running on Glitch.com platform - using memory-only mode"
export MEMORY_ONLY_MODE="True"
export NO_LOCAL_STORAGE="True"
export USE_DROPBOX_STREAMING="True"
export GLITCH_DEPLOYMENT="True"

# Set minimal path for temporary storage if needed
TMP_DIR="/tmp"
export TMP_DIR

# No directories needed in memory-only mode with Dropbox
echo "No local directories needed - running in pure memory mode for Glitch"

# Set up NLTK for streaming access to resources
echo "Configuring NLTK for streaming access..."
python -c "
import os
import nltk
import sys

# Setup for memory-only operation
print('Setting up NLTK for memory-only operation with Dropbox')
# NLTK will use the custom provider for resources
# No resources will be downloaded to disk
nltk.data.path.append('memory:')
print(f'NLTK paths: {nltk.data.path}')
"

# Verify scikit-learn is working
echo "Verifying scikit-learn installation..."
python -c "import sklearn; print(f'scikit-learn version: {sklearn.__version__}')"

# Refresh Dropbox tokens before starting
echo "Running Dropbox token refresh..."
if [ -f "./refresh_token.py" ]; then
    python ./refresh_token.py || echo "Token refresh failed, continuing anyway"
fi

# Display environment summary
echo "Environment summary:"
echo "Running on Glitch.com with memory-only mode"
echo "PORT=${PORT:-3000}"

# Start the application with a single worker to conserve memory
echo "Starting application with Gunicorn (single worker)..."
exec gunicorn --bind 0.0.0.0:${PORT:-3000} --workers ${GUNICORN_WORKERS:-1} --timeout 120 "app:app"
