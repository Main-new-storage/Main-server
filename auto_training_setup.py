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

def ensure_dropbox_folders():
    """
    Ensure all necessary folders exist in Dropbox
    
    This creates the required folder structure in Dropbox that the Colab integration needs:
    - training_triggers folder (for trigger files)
    - backdoor_models folder (for storing trained models)
    - backdoor_models/trained (for storing models trained by Colab)
    - backdoor_models/uploaded (for storing user-uploaded models)
    - base_model folder (for the initial model)
    """
    try:
        import config
        if not config.DROPBOX_ENABLED:
            logger.warning("Dropbox is not enabled - skipping folder creation")
            return False
            
        from utils.dropbox_storage import get_dropbox_storage
        dropbox_storage = get_dropbox_storage()
        
        # Define folders that need to exist
        required_folders = [
            "/training_triggers",
            "/backdoor_models",
            "/backdoor_models/trained",
            "/backdoor_models/uploaded",
            "/base_model"
        ]
        
        # Create each folder if it doesn't exist
        for folder in required_folders:
            try:
                # Check if folder exists
                try:
                    dropbox_storage.dbx.files_get_metadata(folder)
                    logger.info(f"Dropbox folder exists: {folder}")
                except Exception:
                    # Create folder
                    dropbox_storage.dbx.files_create_folder_v2(folder)
                    logger.info(f"Created Dropbox folder: {folder}")
            except Exception as e:
                logger.error(f"Error creating Dropbox folder {folder}: {e}")
        
        # Create a README file in training_triggers to document the purpose
        try:
            readme_content = """# Training Triggers Folder
This folder contains trigger files that signal to Google Colab when training is needed.

## Trigger Files
* Files named `training_needed_*.json` will be detected by Colab
* These files contain metadata about the requested training job
* Status will be updated as training progresses

## Status Values
* `pending` - Training job has been created but not started
* `processing` - Colab has detected the job and is preparing
* `training` - Model training is in progress
* `completed` - Training successfully completed
* `failed` - Training failed to complete

For more information, see the documentation in the colab_integration folder.
"""
            # Convert to bytes
            import io
            readme_buffer = io.BytesIO(readme_content.encode('utf-8'))
            
            # Upload README
            dropbox_storage.dbx.files_upload(
                readme_buffer.getvalue(),
                "/training_triggers/README.md",
                mode=dropbox_storage.dbx.files.WriteMode.overwrite
            )
            logger.info("Created README in training_triggers folder")
            
        except Exception as e:
            logger.error(f"Error creating README file: {e}")
        
        return True
            
    except Exception as e:
        logger.error(f"Error ensuring Dropbox folders: {e}")
        return False

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
                
                # First ensure all required Dropbox folders exist
                logger.info("Creating required Dropbox folders...")
                ensure_dropbox_folders()
                
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
