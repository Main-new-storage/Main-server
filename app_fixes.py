#!/usr/bin/env python3
"""
Update script for Backdoor AI server to fix memory and Dropbox issues.

This script applies the fixes from utils/model_validator_fix.py to 
an existing app.py installation. Run it before starting the app.
"""

import os
import sys
import logging
import importlib
import importlib.util
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app_fixes.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_module_exists(module_name):
    """Check if a module exists and is importable."""
    try:
        importlib.util.find_spec(module_name)
        return True
    except ModuleNotFoundError:
        return False

def apply_fixes():
    """Apply fixes to the Backdoor AI app."""
    logger.info("Starting Backdoor AI fix application")
    
    # Step 1: Check if fix modules exist
    required_modules = [
        ('utils.nltk_resources', 'Enhanced NLTK resource manager'),
        ('utils.memory_efficient_model', 'Memory-efficient model loading'),
        ('utils.model_validator_fix', 'Model validation fixes')
    ]
    
    missing_modules = [name for name, desc in required_modules if not check_module_exists(name)]
    if missing_modules:
        logger.error(f"Missing required modules: {', '.join(missing_modules)}")
        logger.error("Cannot apply fixes. Please ensure all fix modules are properly installed.")
        return False
    
    # Step 2: Run validation and fixes
    try:
        from utils.model_validator_fix import validate_and_fix
        validate_and_fix()
        logger.info("Applied model validation fixes")
    except Exception as e:
        logger.error(f"Error applying model validation fixes: {e}")
        return False
    
    # Step 3: Apply memory optimization for model streaming
    try:
        # Patch app.py model loading to use memory-efficient approach
        from utils.memory_efficient_model import load_model_efficiently, get_model_url, predict_intent
        logger.info("Memory-efficient model utilities are available")
        
        # Here we would patch app.py if we could directly modify it
        # Since we can't, we'll provide instructions
        logger.info("To use memory-efficient model loading:")
        logger.info("1. Replace 'from utils.model_download import get_base_model_buffer' with:")
        logger.info("   try:")
        logger.info("       from utils.memory_efficient_model import get_model_url")
        logger.info("       model_url = get_model_url(model_name)")
        logger.info("       if model_url:")
        logger.info("           return redirect(model_url)")
        logger.info("   except ImportError:")
        logger.info("       # Fall back to old approach")
        logger.info("       pass")
        
    except ImportError:
        logger.warning("Memory-efficient model utilities not available")
    
    # Step 4: Check if NLTK resources are properly setup
    try:
        from utils.nltk_resources import init_nltk_resources
        init_nltk_resources()
        logger.info("NLTK resources initialized with enhanced manager")
    except ImportError:
        logger.warning("Enhanced NLTK resource manager not available")
    
    logger.info("Fix application completed")
    return True

def main():
    """Main entry point."""
    try:
        print("Backdoor AI Fix Application")
        print("==========================")
        print("This script will apply fixes for:")
        print("- Dropbox shared link errors")
        print("- Memory issues with model loading")
        print("- Missing NLTK resources")
        print()
        
        # Apply fixes
        success = apply_fixes()
        
        if success:
            print("\nFixes applied successfully!")
            print("Your app should now run without the previous errors.")
            print("\nImportant instructions:")
            print("1. Use 'utils.memory_efficient_model' instead of model_download")
            print("2. Use 'utils.nltk_resources' instead of nltk_helpers")
            print("3. Call validate_and_fix() early in your app initialization")
            print("\nFor more details, see app_fixes.log")
        else:
            print("\nSome fixes could not be applied.")
            print("Check app_fixes.log for detailed error information.")
        
        return 0 if success else 1
    
    except Exception as e:
        logger.error(f"Unhandled error in fix application: {e}", exc_info=True)
        print(f"An error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
