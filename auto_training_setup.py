#!/usr/bin/env python3
"""
Module to automatically trigger training when app is deployed

This module provides a function to trigger model training when the Flask app
is deployed to Render.com or other platforms. It schedules the training in a
background thread so it doesn't block app startup.
"""

import threading
import time
import logging
from typing import Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def setup_training_on_deploy(delay_seconds: int = 30, force: bool = False) -> None:
    """
    Schedule a training job to run after app deployment
    
    Args:
        delay_seconds: Number of seconds to wait after app startup before triggering training
        force: Whether to force training even if criteria aren't met
    """
    try:
        # Import here to avoid circular imports
        from app_trigger_training import create_trigger_file
        
        def delayed_training_trigger():
            """Run in a separate thread to trigger training after a delay"""
            try:
                # Wait for app to fully initialize
                logger.info(f"Waiting {delay_seconds} seconds before triggering training...")
                time.sleep(delay_seconds)
                
                # Trigger training
                timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                reason = f"app_deployment_{timestamp}"
                
                logger.info(f"Triggering training after deployment: {reason}")
                success = create_trigger_file(reason=reason, force=force)
                
                if success:
                    logger.info("Successfully triggered post-deployment training")
                else:
                    logger.warning("Failed to trigger post-deployment training")
                    
            except Exception as e:
                logger.error(f"Error in training trigger thread: {e}", exc_info=True)
        
        # Start in background thread to not block app startup
        logger.info("Scheduling post-deployment training trigger")
        trigger_thread = threading.Thread(target=delayed_training_trigger)
        trigger_thread.daemon = True  # Thread will exit when app exits
        trigger_thread.start()
        
    except Exception as e:
        logger.error(f"Failed to schedule training on deployment: {e}", exc_info=True)

def check_training_status() -> Optional[dict]:
    """
    Check the current status of training jobs
    
    Returns:
        Dictionary with latest training job info, or None if check fails
    """
    try:
        import json
        import subprocess
        from pathlib import Path
        
        # Path to status script
        script_path = Path(__file__).parent / "colab_integration" / "get_training_status.py"
        
        # Run script in subprocess with JSON output
        result = subprocess.run(
            ["python", str(script_path), "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON output
        status_data = json.loads(result.stdout)
        return status_data
        
    except Exception as e:
        logger.error(f"Failed to check training status: {e}", exc_info=True)
        return None
