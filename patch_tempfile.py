"""
Patch the tempfile module to use virtual in-memory implementations.

This module is used for testing memory-only mode functionality by patching
the standard tempfile module with in-memory implementations that don't
require disk access.
"""

import sys
import logging
from unittest import mock
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import the virtual tempfile implementation 
from utils.virtual_tempfile import NamedTemporaryFile, mkdtemp, mkstemp, gettempdir

def patch_tempfile():
    """
    Patch the tempfile module with virtual implementations.
    
    This replaces the standard disk-based tempfile functions with
    in-memory implementations for testing in memory-only environments.
    """
    try:
        # Check if tempfile is already imported
        if 'tempfile' in sys.modules:
            tempfile = sys.modules['tempfile']
            
            # Patch the module functions
            tempfile.NamedTemporaryFile = NamedTemporaryFile
            tempfile.mkdtemp = mkdtemp
            tempfile.mkstemp = mkstemp
            tempfile.gettempdir = gettempdir
            
            logger.info("Patched existing tempfile module with virtual implementations")
        else:
            # Create a mock module if tempfile hasn't been imported yet
            mock_tempfile = mock.MagicMock()
            mock_tempfile.NamedTemporaryFile = NamedTemporaryFile
            mock_tempfile.mkdtemp = mkdtemp
            mock_tempfile.mkstemp = mkstemp
            mock_tempfile.gettempdir = gettempdir
            
            # Add to sys.modules
            sys.modules['tempfile'] = mock_tempfile
            logger.info("Created virtual tempfile module implementation")
        
        return True
    except Exception as e:
        logger.error(f"Failed to patch tempfile module: {e}")
        return False

def unpatch_tempfile():
    """
    Restore the original tempfile module.
    
    This removes the patches applied by patch_tempfile().
    """
    try:
        # Reload the original module
        import importlib
        sys.modules['tempfile'] = importlib.reload(importlib.import_module('tempfile'))
        logger.info("Restored original tempfile module")
        return True
    except Exception as e:
        logger.error(f"Failed to restore original tempfile module: {e}")
        return False

# Use as context manager
class TempfilePatcher:
    """Context manager for temporarily patching the tempfile module."""
    
    def __enter__(self):
        """Patch tempfile on entry."""
        self.success = patch_tempfile()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original tempfile on exit."""
        if self.success:
            unpatch_tempfile()
