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
print('NLTK paths: %s' % nltk.data.path)
"

# Verify scikit-learn is working
echo "Verifying scikit-learn installation..."
python -c "
import sklearn
print('scikit-learn version: %s' % sklearn.__version__)
"

# Ensure token refresh on startup
echo "Creating token file if missing..."
python -c "
import os
import json
import datetime

# Hardcoded token from config.py 
REFRESH_TOKEN = 'RvyL03RE5qAAAAAAAAAAAVMVebvE7jDx8Okd0ploMzr85c6txvCRXpJAt30mxrKF'
APP_KEY = '2bi422xpd3xd962'
APP_SECRET = 'j3yx0b41qdvfu86'

# Create token file with refresh token
token_file = 'dropbox_tokens.json'
if not os.path.exists(token_file):
    try:
        tokens = {
            'refresh_token': REFRESH_TOKEN,
            'app_key': APP_KEY,
            'app_secret': APP_SECRET,
            'created_at': datetime.datetime.now().isoformat()
        }
        with open(token_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        print('Created token file with refresh token')
    except Exception as e:
        print('Error creating token file: %s' % str(e))
else:
    print('Token file already exists')
"

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
