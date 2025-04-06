"""
Enhanced NLTK resource management for the Backdoor AI server.

This module provides improved NLTK resource handling with:
1. Automatic download and upload of missing resources to Dropbox
2. Efficient caching of resources to minimize memory usage
3. Fallback mechanisms when resources are unavailable
"""

import os
import logging
import tempfile
import zipfile
import io
from typing import List, Dict, Any, Optional, Tuple
import nltk

import config

# Configure logging
logger = logging.getLogger(__name__)

# Define the essential NLTK resources we need
REQUIRED_NLTK_RESOURCES = [
    ('punkt', 'tokenizers/punkt'),
    ('stopwords', 'corpora/stopwords'),
    ('wordnet', 'corpora/wordnet')
]

class NLTKResourceManager:
    """Manages NLTK resources with Dropbox integration."""
    
    def __init__(self, dropbox_storage=None):
        """
        Initialize the NLTK resource manager.
        
        Args:
            dropbox_storage: Dropbox storage instance to use
        """
        self.dropbox_storage = dropbox_storage
        self.resource_cache = {}
        self.initialized = False
        
    def ensure_resources(self, resources: List[Tuple[str, str]] = None) -> bool:
        """
        Ensure all required NLTK resources are available.
        
        Args:
            resources: List of (resource_name, resource_path) tuples to ensure.
                      If None, uses REQUIRED_NLTK_RESOURCES.
        
        Returns:
            bool: True if all resources are available, False otherwise
        """
        if resources is None:
            resources = REQUIRED_NLTK_RESOURCES
            
        success = True
        for resource_name, resource_path in resources:
            if not self.ensure_resource(resource_name, resource_path):
                success = False
                
        self.initialized = success
        return success
        
    def ensure_resource(self, resource_name: str, resource_path: str) -> bool:
        """
        Ensure a specific NLTK resource is available.
        
        Args:
            resource_name: Name of the resource (e.g., 'punkt')
            resource_path: Path to the resource (e.g., 'tokenizers/punkt')
            
        Returns:
            bool: True if the resource is available, False otherwise
        """
        logger.info(f"Ensuring NLTK resource is available: {resource_name}")
        
        # First try to find in Dropbox
        if self.dropbox_storage:
            resource_found = self.find_resource_in_dropbox(resource_name, resource_path)
            if resource_found:
                logger.info(f"Found NLTK resource in Dropbox: {resource_name}")
                return True
        
        # If not in Dropbox, try to download and then upload
        try:
            # Download the resource
            logger.info(f"Downloading NLTK resource: {resource_name}")
            nltk.download(resource_name, quiet=True)
            
            # Try to find the downloaded resource
            try:
                local_path = nltk.data.find(resource_path)
                if local_path:
                    logger.info(f"Found downloaded NLTK resource at: {local_path}")
                    
                    # If we have Dropbox storage, upload the resource
                    if self.dropbox_storage:
                        success = self.upload_resource_to_dropbox(local_path, resource_name, resource_path)
                        if success:
                            logger.info(f"Uploaded NLTK resource to Dropbox: {resource_name}")
                        else:
                            logger.warning(f"Failed to upload NLTK resource to Dropbox: {resource_name}")
                    
                    return True
                else:
                    logger.warning(f"Downloaded NLTK resource but couldn't find path: {resource_name}")
            except LookupError:
                logger.warning(f"Downloaded NLTK resource but path lookup failed: {resource_name}")
        
        except Exception as e:
            logger.error(f"Error ensuring NLTK resource {resource_name}: {e}")
        
        return False
    
    def find_resource_in_dropbox(self, resource_name: str, resource_path: str) -> bool:
        """
        Find an NLTK resource in Dropbox.
        
        Args:
            resource_name: Name of the resource
            resource_path: Path to the resource
            
        Returns:
            bool: True if found, False otherwise
        """
        if not self.dropbox_storage:
            return False
        
        # Try different possible paths
        dropbox_paths = [
            f"/nltk_data/{resource_path}",                      # Standard path
            f"/nltk_data/{os.path.dirname(resource_path)}.zip", # Zipped folder
            f"/nltk_data/{resource_path}.zip"                   # Zipped resource
        ]
        
        for path in dropbox_paths:
            try:
                # Check if file exists in Dropbox
                try:
                    self.dropbox_storage.dbx.files_get_metadata(path)
                    logger.info(f"Found NLTK resource in Dropbox at: {path}")
                    
                    # Register this path with NLTK
                    self._register_dropbox_path(resource_name, path)
                    return True
                except Exception:
                    logger.debug(f"NLTK resource not found at Dropbox path: {path}")
            except Exception as e:
                logger.debug(f"Error checking Dropbox path {path}: {e}")
        
        logger.warning(f"NLTK resource not found in Dropbox: {resource_name}")
        return False
    
    def upload_resource_to_dropbox(self, local_path: str, resource_name: str, resource_path: str) -> bool:
        """
        Upload an NLTK resource to Dropbox.
        
        Args:
            local_path: Local path to the resource
            resource_name: Name of the resource
            resource_path: Standard path of the resource
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        if not self.dropbox_storage:
            return False
        
        try:
            # Determine if it's a file or directory
            if os.path.isdir(local_path):
                # For directories, need to create a zip file
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                    temp_zip_path = temp_zip.name
                
                # Create zip file
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(local_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculate relative path within the zip
                            relative_path = os.path.relpath(file_path, os.path.dirname(local_path))
                            zipf.write(file_path, relative_path)
                
                # Upload zip to Dropbox
                dropbox_path = f"/nltk_data/{os.path.basename(resource_path)}.zip"
                with open(temp_zip_path, 'rb') as f:
                    self.dropbox_storage.dbx.files_upload(
                        f.read(), 
                        dropbox_path,
                        mode=self.dropbox_storage.dbx.files.WriteMode.overwrite
                    )
                
                # Clean up temp file
                try:
                    os.unlink(temp_zip_path)
                except Exception:
                    pass
                
                logger.info(f"Uploaded directory as zip to Dropbox: {dropbox_path}")
                
            else:
                # For files, upload directly
                dropbox_path = f"/nltk_data/{resource_path}"
                
                # Ensure parent directory exists
                parent_dir = os.path.dirname(dropbox_path)
                if parent_dir != "/nltk_data":
                    try:
                        self.dropbox_storage.dbx.files_get_metadata(parent_dir)
                    except Exception:
                        try:
                            self.dropbox_storage.dbx.files_create_folder_v2(parent_dir)
                            logger.info(f"Created directory in Dropbox: {parent_dir}")
                        except Exception as e:
                            logger.warning(f"Error creating directory in Dropbox: {e}")
                
                # Upload file
                with open(local_path, 'rb') as f:
                    self.dropbox_storage.dbx.files_upload(
                        f.read(), 
                        dropbox_path,
                        mode=self.dropbox_storage.dbx.files.WriteMode.overwrite
                    )
                
                logger.info(f"Uploaded file to Dropbox: {dropbox_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error uploading NLTK resource to Dropbox: {e}")
            return False
    
    def _register_dropbox_path(self, resource_name: str, dropbox_path: str) -> None:
        """
        Register a Dropbox path with NLTK data system.
        
        Args:
            resource_name: Resource name
            dropbox_path: Path in Dropbox
        """
        try:
            # Create a custom finder function that retrieves from Dropbox
            def dropbox_finder(resource_name):
                try:
                    # Download file from Dropbox to a temp file or buffer
                    metadata, response = self.dropbox_storage.dbx.files_download(dropbox_path)
                    content = response.content
                    
                    # For zip files, create a special handler
                    if dropbox_path.endswith('.zip'):
                        buffer = io.BytesIO(content)
                        return ZipFilePathPointer(buffer, resource_name)
                    
                    # For regular files, return a buffer
                    return BufferResourcePointer(io.BytesIO(content), metadata.name)
                except Exception as e:
                    logger.error(f"Error in dropbox_finder: {e}")
                    raise
            
            # Register with NLTK
            if hasattr(nltk.data, 'finder') and hasattr(nltk.data.finder, '_find_with_metaclass'):
                # Add as metaclass finder
                class DropboxFinder(nltk.data.finder._find_with_metaclass(type)):
                    @classmethod
                    def find(cls, resource_name):
                        if resource_name.endswith(resource_name):
                            return dropbox_finder(resource_name)
                        return None
                
                nltk.data.finder._resource_finders.append(DropboxFinder)
            
        except Exception as e:
            logger.error(f"Error registering Dropbox path for NLTK: {e}")


class BufferResourcePointer:
    """A resource pointer that reads from a buffer."""
    
    def __init__(self, buffer, name):
        self.buffer = buffer
        self.name = name
        
    def open(self):
        self.buffer.seek(0)
        return self.buffer
    
    def close(self):
        pass


class ZipFilePathPointer:
    """A resource pointer for resources in a zip file."""
    
    def __init__(self, zipfile_buffer, resource_name):
        self.zipfile_buffer = zipfile_buffer
        self.resource_name = resource_name
        self.zipfile = None
        
    def open(self):
        # Create zipfile object from buffer
        self.zipfile_buffer.seek(0)
        self.zipfile = zipfile.ZipFile(self.zipfile_buffer)
        
        # Try to find the resource in the zip
        for name in self.zipfile.namelist():
            if name.endswith(self.resource_name):
                return self.zipfile.open(name)
        
        # If not found, raise error
        raise LookupError(f"Resource {self.resource_name} not found in zip file")
    
    def close(self):
        if self.zipfile:
            self.zipfile.close()


def init_nltk_resources():
    """
    Initialize NLTK resources with automatic download and upload to Dropbox.
    
    This is a more robust function that ensures all required NLTK resources
    are available and properly stored in Dropbox.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Import inside function to avoid circular imports
        from utils.dropbox_storage import get_dropbox_storage
        
        # Get Dropbox storage instance if enabled
        dropbox_storage = None
        if config.DROPBOX_ENABLED:
            try:
                dropbox_storage = get_dropbox_storage()
                logger.info("Got Dropbox storage for NLTK resources")
            except Exception as e:
                logger.warning(f"Could not get Dropbox storage: {e}")
        
        # Create resource manager
        resource_manager = NLTKResourceManager(dropbox_storage)
        
        # Ensure all required resources are available
        success = resource_manager.ensure_resources()
        
        if success:
            logger.info("Successfully initialized all NLTK resources")
        else:
            logger.warning("Some NLTK resources could not be initialized")
        
        return success
    
    except Exception as e:
        logger.error(f"Error initializing NLTK resources: {e}")
        return False
