"""
Path utilities for the RWM dataset tools.
"""
import os
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def create_directory(path: str) -> None:
    """
    Create a directory if it doesn't exist.
    
    Args:
        path: Directory path
    """
    os.makedirs(path, exist_ok=True)
    logger.debug(f"Created directory: {path}")

def create_symlink(source: str, destination: str, overwrite: bool = False) -> None:
    """
    Create a symbolic link.
    
    Args:
        source: Source path
        destination: Destination path
        overwrite: Whether to overwrite an existing link
    """
    # Ensure the source exists
    if not os.path.exists(source):
        logger.warning(f"Source path does not exist: {source}")
        return
        
    # Create parent directory if it doesn't exist
    parent_dir = os.path.dirname(destination)
    create_directory(parent_dir)
    
    # Remove existing link if overwrite is True
    if os.path.exists(destination):
        if overwrite:
            os.remove(destination)
        else:
            logger.debug(f"Destination already exists: {destination}")
            return
    
    # Create the symbolic link
    try:
        os.symlink(source, destination)
        logger.debug(f"Created symlink: {source} -> {destination}")
    except Exception as e:
        logger.error(f"Failed to create symlink: {e}")

def remove_directory(path: str) -> None:
    """
    Remove a directory and all its contents.
    
    Args:
        path: Directory path
    """
    if os.path.exists(path):
        shutil.rmtree(path)
        logger.debug(f"Removed directory: {path}")

def get_file_extension(path: str) -> str:
    """
    Get the file extension of a path.
    
    Args:
        path: File path
        
    Returns:
        File extension (including the dot)
    """
    return os.path.splitext(path)[1]