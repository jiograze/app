"""File utility functions."""
import os
from pathlib import Path
from typing import Optional, Set
from werkzeug.datastructures import FileStorage

def allowed_file(filename: str, allowed_extensions: Optional[Set[str]] = None) -> bool:
    """Check if the file has an allowed extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed file extensions (without leading .)
        
    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    if not filename or '.' not in filename:
        return False
    
    if allowed_extensions is None:
        from flask import current_app
        allowed_extensions = set(current_app.config['ALLOWED_EXTENSIONS'])
    
    return get_file_extension(filename).lower() in allowed_extensions

def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        str: The file extension (without leading .), converted to lowercase
    """
    return Path(filename).suffix[1:].lower()

def get_safe_filename(filename: str) -> str:
    """Generate a safe filename by removing special characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Safe filename with only alphanumeric characters, dots, and underscores
    """
    from werkzeug.utils import secure_filename
    return secure_filename(filename)

def get_mime_type(filename: str) -> str:
    """Get the MIME type of a file based on its extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        str: MIME type string
    """
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        int: File size in bytes
    """
    return os.path.getsize(file_path)

def save_uploaded_file(file: FileStorage, upload_folder: str) -> str:
    """Save an uploaded file to the specified folder.
    
    Args:
        file: Uploaded file
        upload_folder: Directory to save the file in
        
    Returns:
        str: Path to the saved file
    """
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate a unique filename
    filename = get_safe_filename(file.filename)
    unique_id = str(uuid.uuid4())
    file_ext = get_file_extension(filename)
    unique_filename = f"{unique_id}.{file_ext}"
    
    # Save the file
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    return file_path

def delete_file(file_path: str) -> bool:
    """Delete a file if it exists.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        bool: True if the file was deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        logger.error(f'Error deleting file {file_path}: {str(e)}')
        return False
