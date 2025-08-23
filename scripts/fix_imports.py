#!/usr/bin/env python3
"""Script to fix import statements after restructuring the project."""

import os
import re
from pathlib import Path

# Base directory of the project
BASE_DIR = Path('/home/altay/Masaüstü/mevzuat/src/mevzuat')

# Mapping of old import paths to new ones
IMPORT_MAPPINGS = {
    # Old pattern: New pattern
    'from app.core.': 'from mevzuat.core.',
    'from core.': 'from mevzuat.core.',
    'from ..core.': 'from mevzuat.core.',
    'from ...core.': 'from mevzuat.core.',
    'from .core.': 'from mevzuat.core.',
    'from ui.': 'from mevzuat.ui.',
    'from ..ui.': 'from mevzuat.ui.',
    'from ...ui.': 'from mevzuat.ui.',
    'from .ui.': 'from mevzuat.ui.',
    'from utils.': 'from mevzuat.utils.',
    'from ..utils.': 'from mevzuat.utils.',
    'from ...utils.': 'from mevzuat.utils.',
    'from .utils.': 'from mevzuat.utils.',
    'from monitoring.': 'from mevzuat.monitoring.',
    'from ..monitoring.': 'from mevzuat.monitoring.',
    'from ...monitoring.': 'from mevzuat.monitoring.',
    'from .monitoring.': 'from mevzuat.monitoring.',
    'from training.': 'from mevzuat.training.',
    'from ..training.': 'from mevzuat.training.',
    'from ...training.': 'from mevzuat.training.',
    'from .training.': 'from mevzuat.training.',
    'from models.': 'from mevzuat.models.',
    'from ..models.': 'from mevzuat.models.',
    'from ...models.': 'from mevzuat.models.',
    'from .models.': 'from mevzuat.models.',
    'from services.': 'from mevzuat.services.',
    'from ..services.': 'from mevzuat.services.',
    'from ...services.': 'from mevzuat.services.',
    'from .services.': 'from mevzuat.services.',
    'from web.': 'from mevzuat.web.',
    'from ..web.': 'from mevzuat.web.',
    'from ...web.': 'from mevzuat.web.',
    'from .web.': 'from mevzuat.web.',
    'from api.': 'from mevzuat.api.',
    'from ..api.': 'from mevzuat.api.',
    'from ...api.': 'from mevzuat.api.',
    'from .api.': 'from mevzuat.api.',
}

def update_imports_in_file(file_path):
    """Update import statements in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update imports based on the mapping
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)
        
        # Fix relative imports that might be broken
        content = re.sub(
            r'from (\s*)mevzuat\.mevzuat\.', 
            r'from \1mevzuat.', 
            content
        )
        
        # Only write if there were changes
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to update imports in all Python files."""
    updated_files = 0
    
    # Process all Python files in the project
    for py_file in BASE_DIR.rglob('*.py'):
        if update_imports_in_file(py_file):
            print(f"Updated imports in: {py_file.relative_to(BASE_DIR)}")
            updated_files += 1
    
    print(f"\nUpdated imports in {updated_files} files.")

if __name__ == "__main__":
    main()
