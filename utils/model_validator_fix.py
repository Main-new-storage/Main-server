"""
Enhanced model validator and diagnostic tools for Backdoor AI server.

This module adds fixes to the model validation process:
1. Uses shared links more efficiently to avoid Dropbox errors
2. Avoids loading models fully into memory to prevent OOM errors
3. Automatically creates an NLTK resources folder in Dropbox
"""

import logging
from typing import Dict, Any, Optional

import config

# Configure logging
logger = logging.getLogger(__name__)

def validate_and_fix():
    """
    Run an enhanced model validation process that fixes common issues:
    1. Shared link errors by checking existing links
    2. Memory usage by streaming models instead of loading them fully
    3. NLTK resource issues by creating proper folders and downloading resources
    
    Call this function early in app initialization to fix potential problems.
    """
    logger.info("Starting enhanced model validation and diagnostic fixes")
    
    # Step 1: Fix NLTK resources
    fix_nltk_resources()
    
    # Step 2: Fix model validation to use memory-efficient approach
    fix_model_validation()
    
    # Step 3: Ensure Dropbox folders exist for training
    ensure_dropbox_folders()
    
    logger.info("Completed enhanced validation and fixes")

def fix_nltk_resources() -> bool:
    """Fix NLTK resource issues by ensuring resources exist in Dropbox."""
    try:
        # Check if our enhanced NLTK resources module is available
        try:
            from utils.nltk_resources import init_nltk_resources
            
            # Initialize with enhanced manager
            success = init_nltk_resources()
            if success:
                logger.info("Successfully fixed NLTK resources with enhanced manager")
                return True
            else:
                logger.warning("Could not fully fix NLTK resources with enhanced manager")
                return False
                
        except ImportError:
            logger.warning("Enhanced NLTK resource manager not available - skipping fixes")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing NLTK resources: {e}")
        return False

def fix_model_validation() -> bool:
    """
    Fix model validation to use memory-efficient approach.
    
    This prevents out-of-memory errors by:
    1. Using streaming instead of full model loading
    2. Validating model structure without loading the full model
    3. Using existing shared links instead of creating new ones
    """
    try:
        # Check if our memory-efficient model utilities are available
        try:
            from utils.memory_efficient_model import load_model_efficiently
            
            # Run validation with memory-efficient approach
            base_model_name = getattr(config, 'BASE_MODEL_NAME', 'model_1.0.0.mlmodel')
            result = load_model_efficiently(base_model_name, validation_only=True)
            
            if result['success']:
                logger.info(f"Successfully validated model {base_model_name} with memory-efficient approach")
                return True
            else:
                logger.warning(f"Memory-efficient validation had issues: {', '.join(result.get('errors', []))}")
                return False
                
        except ImportError:
            logger.warning("Memory-efficient model utilities not available - skipping fixes")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing model validation: {e}")
        return False

def ensure_dropbox_folders() -> bool:
    """
    Ensure all required Dropbox folders exist for training.
    
    This prevents errors with missing folders for:
    1. NLTK resources
    2. Training triggers
    3. Model storage
    """
    if not config.DROPBOX_ENABLED:
        logger.info("Dropbox not enabled - skipping folder creation")
        return False
        
    try:
        # Import Dropbox storage
        from utils.dropbox_storage import get_dropbox_storage
        
        # Get Dropbox storage instance
        dropbox_storage = get_dropbox_storage()
        
        # Define folders that need to exist
        required_folders = [
            "/nltk_data",
            "/nltk_data/tokenizers",
            "/nltk_data/corpora",
            "/training_triggers",
            f"/{config.DROPBOX_MODELS_FOLDER}",
            f"/{config.DROPBOX_MODELS_FOLDER}/trained",
            f"/{config.DROPBOX_MODELS_FOLDER}/uploaded",
            f"/{config.DROPBOX_BASE_MODEL_FOLDER}"
        ]
        
        # Create each folder if it doesn't exist
        for folder in required_folders:
            try:
                # Check if folder exists
                try:
                    dropbox_storage.dbx.files_get_metadata(folder)
                    logger.debug(f"Dropbox folder exists: {folder}")
                except Exception:
                    # Create folder
                    dropbox_storage.dbx.files_create_folder_v2(folder)
                    logger.info(f"Created Dropbox folder: {folder}")
            except Exception as e:
                logger.error(f"Error creating Dropbox folder {folder}: {e}")
        
        logger.info("Successfully ensured all required Dropbox folders exist")
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring Dropbox folders: {e}")
        return False
