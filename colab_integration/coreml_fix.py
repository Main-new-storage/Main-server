"""
CoreML compatibility fixes for Backdoor AI Trainer.

This module provides workarounds for common CoreML issues when running in Google Colab,
particularly when dealing with version compatibility problems.
"""

import logging
import os
import sys
import tempfile
import json
import importlib
from typing import Dict, Any, Optional, Tuple, List, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_coreml_environment():
    """
    Apply fixes to the CoreML environment to ensure compatibility.
    
    This function:
    1. Checks CoreML installation status
    2. Fixes import paths if needed
    3. Handles version compatibility issues
    """
    try:
        # First check if we can import coremltools
        try:
            import coremltools as ct
            logger.info(f"CoreML version: {ct.__version__}")
        except ImportError as e:
            logger.error(f"Error importing coremltools: {e}")
            
            # Try to fix coremltools installation
            logger.info("Attempting to fix coremltools installation...")
            fix_coreml_installation()
            return
            
        # Check for missing libcoremlpython
        if not has_libcoremlpython():
            logger.warning("Missing libcoremlpython - trying to fix...")
            fix_libcoremlpython()
            
        # Apply patches for version warnings
        patch_coreml_version_checks()
        
        logger.info("CoreML environment fixes applied")
        
    except Exception as e:
        logger.error(f"Failed to fix CoreML environment: {e}")

def has_libcoremlpython() -> bool:
    """Check if the libcoremlpython module is available."""
    try:
        # Try to import the module
        import coremltools.libcoremlpython
        return True
    except ImportError:
        return False

def fix_coreml_installation():
    """Attempt to fix coremltools installation."""
    try:
        logger.info("Reinstalling coremltools...")
        
        # Uninstall current version
        os.system("pip uninstall -y coremltools")
        
        # Install known good version
        os.system("pip install coremltools==6.3 --no-binary coremltools")
        
        # Reload coremltools
        if 'coremltools' in sys.modules:
            del sys.modules['coremltools']
        
        try:
            import coremltools as ct
            logger.info(f"Successfully reinstalled coremltools {ct.__version__}")
        except ImportError as e:
            logger.error(f"Failed to reinstall coremltools: {e}")
            
    except Exception as e:
        logger.error(f"Error fixing coremltools installation: {e}")

def fix_libcoremlpython():
    """Attempt to fix missing libcoremlpython module."""
    try:
        logger.info("Applying libcoremlpython fix...")
        
        # Create a simple mock module for libcoremlpython
        mock_code = """
class MockProxy:
    def __init__(self, *args, **kwargs):
        pass
        
    def __getattr__(self, name):
        def mock_method(*args, **kwargs):
            return None
        return mock_method

# Create mock proxies
_MLModelProxy = MockProxy
_MLComputePlanProxy = MockProxy
_MLModelAssetProxy = MockProxy
_MLCPUComputeDeviceProxy = MockProxy
_MLGPUComputeDeviceProxy = MockProxy
_MLNeuralEngineComputeDeviceProxy = MockProxy
"""
        
        # Try to find coremltools package location
        import coremltools
        package_dir = os.path.dirname(coremltools.__file__)
        
        # Create the mock module
        mock_path = os.path.join(package_dir, "libcoremlpython.py")
        with open(mock_path, "w") as f:
            f.write(mock_code)
            
        logger.info(f"Created mock libcoremlpython module at {mock_path}")
        
        # Force Python to reload the module
        if 'coremltools.libcoremlpython' in sys.modules:
            del sys.modules['coremltools.libcoremlpython']
            
        # Try to import the mock module
        try:
            import coremltools.libcoremlpython
            logger.info("Successfully loaded mock libcoremlpython module")
        except ImportError as e:
            logger.error(f"Failed to load mock module: {e}")
            
    except Exception as e:
        logger.error(f"Error fixing libcoremlpython: {e}")

def patch_coreml_version_checks():
    """Patch coremltools version compatibility checks."""
    try:
        import coremltools
        
        # Only apply patch if coremltools has the _dependency_check module
        if hasattr(coremltools, '_dependency_check'):
            logger.info("Patching coremltools version checks...")
            
            # Monkey patch the version warning functions
            def dummy_check(*args, **kwargs):
                return True
                
            # Replace version checks with dummy function
            if hasattr(coremltools._dependency_check, 'verify_scikit_learn_version'):
                coremltools._dependency_check.verify_scikit_learn_version = dummy_check
                
            if hasattr(coremltools._dependency_check, 'verify_tensorflow_version'):
                coremltools._dependency_check.verify_tensorflow_version = dummy_check
                
            if hasattr(coremltools._dependency_check, 'verify_torch_version'):
                coremltools._dependency_check.verify_torch_version = dummy_check
                
            if hasattr(coremltools._dependency_check, 'verify_xgboost_version'):
                coremltools._dependency_check.verify_xgboost_version = dummy_check
                
            logger.info("Successfully patched coremltools version checks")
            
    except Exception as e:
        logger.error(f"Failed to patch coremltools version checks: {e}")

def safe_convert_to_coreml(model, 
                           inputs: List[Tuple[str, Any]], 
                           outputs: List[Tuple[str, Any]],
                           fallback_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Safely convert a model to CoreML with fallbacks.
    
    Args:
        model: Model function or object to convert
        inputs: List of (name, type) tuples for inputs
        outputs: List of (name, type) tuples for outputs
        fallback_path: Path to a fallback CoreML model if conversion fails
        
    Returns:
        Dict with success status and model or error
    """
    result = {
        'success': False,
        'model': None,
        'error': None
    }
    
    try:
        # Try to import coremltools
        try:
            import coremltools as ct
            logger.info(f"Using coremltools version {ct.__version__}")
        except ImportError as e:
            error = f"CoreMLTools not available: {e}"
            result['error'] = error
            logger.error(error)
            return result
            
        # Apply fixes to coremltools environment
        fix_coreml_environment()
        
        # Format inputs and outputs for conversion
        ct_inputs = []
        for name, input_type in inputs:
            if isinstance(input_type, str) and input_type == 'str':
                ct_inputs.append(ct.TensorType(shape=(1,), dtype=str, name=name))
            else:
                ct_inputs.append(ct.TensorType(name=name))
                
        ct_outputs = []
        for name, output_type in outputs:
            if isinstance(output_type, str) and output_type == 'str':
                ct_outputs.append(ct.TensorType(dtype=str, name=name))
            elif isinstance(output_type, str) and output_type == 'float32':
                ct_outputs.append(ct.TensorType(dtype='float32', name=name))
            else:
                ct_outputs.append(ct.TensorType(name=name))
        
        # Try direct conversion
        try:
            logger.info("Attempting CoreML conversion...")
            coreml_model = ct.convert(
                model,
                inputs=ct_inputs,
                outputs=ct_outputs
            )
            
            result['model'] = coreml_model
            result['success'] = True
            logger.info("Model conversion successful")
            
        except Exception as direct_error:
            logger.warning(f"Direct conversion failed: {direct_error}")
            
            # Try alternative approach with minimum options
            try:
                logger.info("Trying simplified conversion...")
                # Create simpler conversion with minimum options
                coreml_model = ct.convert(
                    model,
                    inputs=[ct.TensorType(shape=(1,), dtype=str)],
                    outputs=[ct.TensorType(name='output')]
                )
                
                result['model'] = coreml_model
                result['success'] = True
                result['warning'] = "Used simplified conversion due to errors"
                logger.info("Simplified model conversion successful")
                
            except Exception as alt_error:
                # If we have a fallback path, try to load that
                if fallback_path and os.path.exists(fallback_path):
                    try:
                        logger.info(f"Loading fallback model from {fallback_path}")
                        fallback_model = ct.models.MLModel(fallback_path)
                        
                        result['model'] = fallback_model
                        result['success'] = True
                        result['warning'] = "Used fallback model due to conversion errors"
                        logger.info("Fallback model loaded successfully")
                        
                    except Exception as fallback_error:
                        error = f"All conversion attempts failed. Direct: {direct_error}, Alt: {alt_error}, Fallback: {fallback_error}"
                        result['error'] = error
                        logger.error(error)
                else:
                    error = f"Conversion failed and no fallback available. Direct: {direct_error}, Alt: {alt_error}"
                    result['error'] = error
                    logger.error(error)
    
    except Exception as e:
        error = f"Unexpected error in CoreML conversion: {e}"
        result['error'] = error
        logger.error(error)
    
    return result

# Apply fixes when this module is imported
fix_coreml_environment()
