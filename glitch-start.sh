#!/bin/bash
set -e

echo "Starting Backdoor AI Learning Server on Glitch.com..."

# Detect Python version
PYTHON_VERSION=$(python -c "import sys; print('%s.%s' % (sys.version_info[0], sys.version_info[1]))" 2>/dev/null || echo "unknown")
echo "Detected Python $PYTHON_VERSION"

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

# Install core dependencies if they're not available
echo "Checking for essential packages..."
python -c "
try:
    import nltk
    print('NLTK is already installed')
except ImportError:
    import subprocess, sys
    print('Installing NLTK package...')
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'nltk'])
        print('NLTK installed successfully')
    except Exception as e:
        print('Failed to install NLTK: %s' % str(e))
        
try:
    import dropbox
    print('Dropbox is already installed')
except ImportError:
    import subprocess, sys
    print('Installing Dropbox package...')
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'dropbox'])
        print('Dropbox installed successfully')
    except Exception as e:
        print('Failed to install Dropbox: %s' % str(e))
"

# Set up NLTK for streaming access to resources with error handling
echo "Configuring NLTK for streaming access..."
python -c "
import os
import sys

# Try to import NLTK with error handling
try:
    import nltk
    print('Setting up NLTK for memory-only operation with Dropbox')
    # NLTK will use the custom provider for resources
    # No resources will be downloaded to disk
    nltk.data.path.append('memory:')
    print('NLTK paths: %s' % nltk.data.path)
except ImportError:
    print('NLTK module not available - skipping NLTK configuration')
except Exception as e:
    print('Error configuring NLTK: %s' % str(e))
"

# Create memory-only folders
echo "Creating memory-only folders..."
mkdir -p /tmp/nltk_data /tmp/data /tmp/models 2>/dev/null || true

# Try to validate scikit-learn, but handle failure gracefully
echo "Verifying scikit-learn installation..."
python -c "
try:
    import sklearn
    print('scikit-learn version: %s' % sklearn.__version__)
except ImportError:
    print('scikit-learn is not installed')
except Exception as e:
    print('Error checking scikit-learn: %s' % str(e))
"

# Ensure token refresh on startup with graceful error handling
echo "Creating token file if missing..."
python -c "
import os
import json
import sys

# Try to import datetime with error handling for Python 2
try:
    import datetime
except ImportError:
    print('datetime module not available')
    sys.exit(0)

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

# Save hardcoded credentials to environment for direct access
export DROPBOX_APP_KEY="2bi422xpd3xd962"
export DROPBOX_APP_SECRET="j3yx0b41qdvfu86"
export DROPBOX_REFRESH_TOKEN="RvyL03RE5qAAAAAAAAAAAVMVebvE7jDx8Okd0ploMzr85c6txvCRXpJAt30mxrKF"

# Refresh Dropbox tokens before starting
echo "Running Dropbox token refresh..."
if [ -f "./refresh_token.py" ]; then
    python ./refresh_token.py || echo "Token refresh failed, continuing anyway"
fi

# Display environment summary
echo "Environment summary:"
echo "Running on Glitch.com with memory-only mode"
echo "Python version: $PYTHON_VERSION"
echo "PORT=${PORT:-3000}"

# Create a simple health check endpoint to ensure app is running
cat > health_check.py << 'EOL'
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'Backdoor AI Learning Server is running'

@app.route('/health')
def health():
    return 'OK'

if __name__ == '__main__':
    try:
        from app import app as main_app
        import config
        print("Main app imported successfully")
        # Try to add our routes to the main app
        main_app.add_url_rule('/health', 'health', health)
        app = main_app
    except Exception as e:
        print("Couldn't import main app, using minimal app: %s" % e)
    
    app.run(host='0.0.0.0', port=3000)
EOL

# Try main app first, fall back to minimal app if it fails
echo "Starting application..."
if [ -f "app.py" ]; then
    echo "Using main application (app.py)"
    exec gunicorn --bind 0.0.0.0:${PORT:-3000} --workers ${GUNICORN_WORKERS:-1} --timeout 120 "app:app" || python health_check.py
else
    echo "Main application not found, using minimal health check app"
    python health_check.py
fi
