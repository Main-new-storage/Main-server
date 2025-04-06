"""
Memory-efficient model loading and validation for Backdoor AI server.

This module provides optimized methods for working with CoreML models without
loading the entire model into memory, which helps avoid out-of-memory errors
on Render's limited memory environment.
"""

import io
import os
import logging
import time
import tempfile
import requests
from typing import Dict, Any, Optional, Tuple, List, Callable
import threading
from datetime import datetime

import config

# Configure logging
logger = logging.getLogger(__name__)

# Global model cache to avoid reloading
model_cache = {}
model_cache_lock = threading.RLock()

def load_model_efficiently(model_name: str, validation_only: bool = False) -> Dict[str, Any]:
    """
    Load a model in a memory-efficient way, avoiding full model loading when possible.
    
    Args:
        model_name: Name of the model file to load
        validation_only: If True, only validate structure without loading fully
        
    Returns:
        Dict with model info and result status
    """
    start_time = time.time()
    
    # Check cache first
    global model_cache
    with model_cache_lock:
        cached_model = model_cache.get(model_name)
        if cached_model and not validation_only:
            logger.info(f"Using cached model: {model_name}")
            return {
                'success': True,
                'model': cached_model.get('model'),
                'metadata': cached_model.get('metadata', {}),
                'from_cache': True,
                'load_time': time.time() - start_time
            }
    
    result = {
        'success': False,
        'model': None,
        'metadata': {},
        'errors': [],
        'warnings': [],
        'from_cache': False,
        'load_time': 0
    }
    
    try:
        # First get model URL without loading the full model
        model_url = get_model_url(model_name)
        if not model_url:
            error = f"Could not get download URL for model {model_name}"
            result['errors'].append(error)
            logger.error(error)
            return result
            
        result['download_url'] = model_url
        
        # For validation only, just check the model exists and get metadata
        if validation_only:
            logger.info(f"Validation only - skipping full model loading for {model_name}")
            
            # Try to get model metadata by examining just the header
            metadata = get_model_metadata(model_url)
            if metadata:
                result['metadata'] = metadata
                result['success'] = True
                logger.info(f"Successfully validated model {model_name} without loading")
            else:
                error = f"Could not validate model {model_name} metadata"
                result['errors'].append(error)
                logger.warning(error)
            
            result['load_time'] = time.time() - start_time
            return result
        
        # For actual use, we need to load the model
        # Try to use streaming approach to reduce memory usage
        try:
            # Import coremltools carefully
            try:
                import coremltools as ct
                logger.debug("CoreMLTools imported successfully")
            except ImportError:
                error = "CoreMLTools not available, cannot load model"
                result['errors'].append(error)
                logger.error(error)
                return result
            
            # Check for memory-only mode
            memory_only_mode = os.environ.get('MEMORY_ONLY_MODE') == 'True'
            
            if memory_only_mode:
                # Use virtual_tempfile approach
                from utils.virtual_tempfile import NamedTemporaryFile
                
                # This method loads the model in a streaming fashion without 
                # loading the entire file into memory at once
                logger.info(f"Loading model {model_name} using virtual tempfile")
                
                # Download directly into virtual temp file to minimize memory use
                with requests.get(model_url, stream=True) as response:
                    if response.status_code == 200:
                        # Get content size for logging
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        # Use virtual tempfile
                        with NamedTemporaryFile(suffix=".mlmodel") as tmp:
                            # Stream in chunks to avoid loading all at once
                            for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                                if chunk:
                                    tmp.write(chunk)
                                    downloaded += len(chunk)
                                    
                                    # Log progress for large models
                                    if total_size > 0 and downloaded % (20*1024*1024) == 0:  # Log every 20MB
                                        logger.info(f"Downloaded {downloaded/(1024*1024):.1f}MB of {total_size/(1024*1024):.1f}MB")
                            
                            # Now load the model from the virtual temp file
                            logger.info(f"Successfully downloaded {downloaded/(1024*1024):.1f}MB to virtual tempfile")
                            model = ct.models.MLModel(tmp)
                    else:
                        error = f"Error downloading model: HTTP {response.status_code}"
                        result['errors'].append(error)
                        logger.error(error)
                        return result
            else:
                # Use regular tempfile approach
                logger.info(f"Loading model {model_name} using standard tempfile")
                
                # Create a tempfile to store the model
                with tempfile.NamedTemporaryFile(suffix=".mlmodel", delete=False) as tmp:
                    tmp_path = tmp.name
                
                # Download the model to the tempfile
                try:
                    with requests.get(model_url, stream=True) as response:
                        if response.status_code == 200:
                            with open(tmp_path, 'wb') as f:
                                # Stream in chunks to avoid loading all at once
                                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                                    if chunk:
                                        f.write(chunk)
                            
                            # Now load the model from the tempfile
                            model = ct.models.MLModel(tmp_path)
                        else:
                            error = f"Error downloading model: HTTP {response.status_code}"
                            result['errors'].append(error)
                            logger.error(error)
                            return result
                finally:
                    # Clean up the tempfile
                    try:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    except Exception as e:
                        logger.warning(f"Could not remove tempfile {tmp_path}: {e}")
            
            # Extract metadata from the model
            result['metadata'] = {
                'description': getattr(model, 'short_description', ''),
                'license': getattr(model, 'license', ''),
                'version': model.user_defined_metadata.get('version', '1.0.0') if hasattr(model, 'user_defined_metadata') else '1.0.0'
            }
            
            # Store in cache for future use
            with model_cache_lock:
                model_cache[model_name] = {
                    'model': model,
                    'metadata': result['metadata'],
                    'loaded_at': datetime.now().isoformat()
                }
            
            # Success!
            result['model'] = model
            result['success'] = True
            logger.info(f"Successfully loaded model {model_name}")
            
        except Exception as e:
            error = f"Error loading model {model_name}: {str(e)}"
            result['errors'].append(error)
            logger.error(error)
    
    except Exception as e:
        error = f"Unexpected error loading model {model_name}: {str(e)}"
        result['errors'].append(error)
        logger.error(error)
    
    result['load_time'] = time.time() - start_time
    return result

def get_model_url(model_name: str) -> Optional[str]:
    """
    Get the download URL for a model without loading it.
    
    Args:
        model_name: Name of the model file
        
    Returns:
        URL to download the model or None if not found
    """
    try:
        # Import here to avoid circular imports
        from utils.dropbox_storage import get_dropbox_storage
        
        # Get model streaming info
        dropbox_storage = get_dropbox_storage()
        
        # Try in different folders
        folders_to_try = [
            None,  # Default models folder
            "base_model"  # Base model folder
        ]
        
        for folder in folders_to_try:
            try:
                stream_info = dropbox_storage.get_model_stream(model_name, folder=folder)
                if stream_info and stream_info.get('success') and 'download_url' in stream_info:
                    logger.info(f"Found model {model_name} URL in folder {folder or 'default'}")
                    return stream_info['download_url']
            except Exception as e:
                logger.debug(f"Could not get model stream for {model_name} in folder {folder}: {e}")
        
        logger.warning(f"Could not find download URL for model {model_name}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting model URL: {e}")
        return None

def get_model_metadata(url: str) -> Optional[Dict[str, Any]]:
    """
    Get model metadata by examining just the header without downloading the whole file.
    
    Args:
        url: URL to the model file
        
    Returns:
        Dict of metadata or None if unavailable
    """
    try:
        # Get just the headers
        head_response = requests.head(url)
        if head_response.status_code != 200:
            logger.warning(f"Failed to get model headers: HTTP {head_response.status_code}")
            return None
            
        # Extract basic metadata from headers
        metadata = {
            'content_type': head_response.headers.get('Content-Type', 'application/octet-stream'),
            'file_size': int(head_response.headers.get('Content-Length', 0)),
            'last_modified': head_response.headers.get('Last-Modified', ''),
            'etag': head_response.headers.get('ETag', '')
        }
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error getting model metadata: {e}")
        return None

def predict_intent(text: str, model_name: str = None) -> Dict[str, Any]:
    """
    Use a model to predict intent without loading the full model if possible.
    
    Args:
        text: Text to predict intent for
        model_name: Name of the model to use, or None for default
        
    Returns:
        Dict with prediction results
    """
    if model_name is None:
        model_name = getattr(config, 'BASE_MODEL_NAME', 'model_1.0.0.mlmodel')
    
    result = {
        'success': False,
        'intent': None,
        'probabilities': {},
        'errors': []
    }
    
    # Load model efficiently
    model_info = load_model_efficiently(model_name)
    if not model_info['success']:
        result['errors'].extend(model_info['errors'])
        logger.error(f"Failed to load model for prediction: {', '.join(model_info['errors'])}")
        return result
    
    model = model_info['model']
    
    # Preprocess text if needed
    try:
        from learning import preprocessor
        processed_text = preprocessor.preprocess_text(text)
    except ImportError:
        # Simple fallback if preprocessor not available
        processed_text = text.lower()
    
    # Make prediction
    try:
        # If model has predict method, use it directly
        if hasattr(model, 'predict'):
            prediction = model.predict({'text': processed_text})
            
            # Extract intent and probabilities
            if isinstance(prediction, dict):
                # Handle different output formats
                if 'intent' in prediction:
                    result['intent'] = prediction['intent']
                    
                    # Get probabilities if available
                    if 'probabilities' in prediction:
                        probs = prediction['probabilities']
                        if isinstance(probs, dict):
                            result['probabilities'] = probs
                        elif isinstance(probs, list) and hasattr(model, 'classes_'):
                            # Convert list to dict
                            classes = getattr(model, 'classes_', [])
                            result['probabilities'] = dict(zip(classes, probs))
            
            result['success'] = result['intent'] is not None
            
        # Handle other model types if needed
        else:
            result['errors'].append("Unsupported model type - no predict method")
            logger.error("Unsupported model type - no predict method")
            
    except Exception as e:
        error = f"Error making prediction: {str(e)}"
        result['errors'].append(error)
        logger.error(error)
    
    return result
