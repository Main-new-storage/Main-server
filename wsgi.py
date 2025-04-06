import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Import Flask app
from app import app

if __name__ == "__main__":
    # Get port from environment variable
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting WSGI server on port {port}")
    
    # Explicitly bind to 0.0.0.0 to listen on all interfaces
    app.run(host='0.0.0.0', port=port)
    
    # This should not be reached under normal operation
    logger.error("Server unexpectedly stopped!")
