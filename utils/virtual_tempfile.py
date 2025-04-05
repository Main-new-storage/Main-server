"""
Virtual temporary file utilities for Backdoor AI server.

This module provides a virtual version of the tempfile module for use in 
memory-only environments where disk access is not desired or available.
"""

import io
import os
import uuid
import logging
from typing import Optional, Any, BinaryIO, List

logger = logging.getLogger(__name__)

class NamedTemporaryFile:
    """
    A memory-only implementation of NamedTemporaryFile.
    
    This class provides the same interface as tempfile.NamedTemporaryFile
    but doesn't write to disk, storing all data in memory instead.
    """
    
    def __init__(self, 
                 mode: str = 'w+b', 
                 buffering: int = -1, 
                 encoding: Optional[str] = None, 
                 newline: Optional[str] = None, 
                 suffix: Optional[str] = None, 
                 prefix: Optional[str] = None, 
                 dir: Optional[str] = None, 
                 delete: bool = True,
                 **kwargs):
        """
        Initialize a virtual temporary file.
        
        Args:
            mode: File mode, should be 'w+b' for binary mode or 'w+' for text mode
            buffering: Ignored, included for compatibility
            encoding: Encoding for text mode
            newline: Newline conversion mode
            suffix: Optional suffix for the filename
            prefix: Optional prefix for the filename
            dir: Ignored, included for compatibility
            delete: Ignored, included for compatibility
            **kwargs: Additional arguments for compatibility
        """
        self.name = f"/virtual/temp/{prefix or 'tmp'}_{uuid.uuid4().hex}{suffix or ''}"
        self.mode = mode
        self.encoding = encoding
        self.newline = newline
        self.closed = False
        self.delete = delete
        
        # Create in-memory buffer
        self._buffer = io.BytesIO()
        
        logger.debug(f"Created virtual temporary file: {self.name}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def write(self, data):
        """
        Write data to the temporary file.
        
        Args:
            data: Data to write (bytes or string)
            
        Returns:
            int: Number of bytes written
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")
            
        # Convert string to bytes if in text mode
        if 'b' not in self.mode and isinstance(data, str):
            encoding = self.encoding or 'utf-8'
            data = data.encode(encoding)
        
        return self._buffer.write(data)
    
    def read(self, size: int = -1):
        """
        Read data from the temporary file.
        
        Args:
            size: Number of bytes to read (None for all)
            
        Returns:
            bytes or str: Data read from file
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")
        
        data = self._buffer.read(size)
        
        # Convert bytes to string in text mode
        if 'b' not in self.mode and isinstance(data, bytes):
            encoding = self.encoding or 'utf-8'
            return data.decode(encoding)
        
        return data
    
    def seek(self, offset, whence=0):
        """
        Change the stream position.
        
        Args:
            offset: Offset in bytes
            whence: Position reference (0=start, 1=current, 2=end)
            
        Returns:
            int: New absolute position
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")
        
        return self._buffer.seek(offset, whence)
    
    def tell(self):
        """
        Return current stream position.
        
        Returns:
            int: Current position
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")
        
        return self._buffer.tell()
    
    def flush(self):
        """Flush the write buffers (no-op for in-memory files)."""
        pass
    
    def close(self):
        """Close the file."""
        if not self.closed:
            self.closed = True
            self._buffer.close()
    
    def getvalue(self):
        """
        Get the current contents of the buffer.
        
        Returns:
            bytes: The current contents of the buffer
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")
        
        # Save the current position
        pos = self._buffer.tell()
        
        # Read the entire buffer
        self._buffer.seek(0)
        value = self._buffer.getvalue()
        
        # Restore the position
        self._buffer.seek(pos)
        
        return value

def mkdtemp(suffix=None, prefix=None, dir=None):
    """
    Create a virtual temporary directory (simulated).
    
    Returns:
        str: Virtual directory path
    """
    temp_dir = f"/virtual/temp/{prefix or 'dir'}_{uuid.uuid4().hex}{suffix or ''}"
    logger.debug(f"Created virtual temporary directory: {temp_dir}")
    return temp_dir

def mkstemp(suffix=None, prefix=None, dir=None, text=False):
    """
    Create a virtual temporary file (simulated).
    
    Returns:
        tuple: (file descriptor (always -1 since virtual), file path)
    """
    temp_file = f"/virtual/temp/{prefix or 'file'}_{uuid.uuid4().hex}{suffix or ''}"
    logger.debug(f"Created virtual temporary file descriptor: {temp_file}")
    return (-1, temp_file)

# For compatibility with the tempfile module
gettempdir = lambda: "/virtual/temp"
