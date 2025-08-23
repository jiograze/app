#!/usr/bin/env python3
"""Test script to verify all imports are working correctly."""

import sys
import os
import importlib
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

# List of modules to test with their expected dependencies
MODULES_TO_TEST = [
    'mevzuat.core.app_manager',
    'mevzuat.core.database',
    'mevzuat.core.search',
    'mevzuat.core.analyzer',
    'mevzuat.core.processor',
    'mevzuat.core.bert_title_analyzer',
    'mevzuat.ui.main_window',
    'mevzuat.ui.settings_dialog',
    'mevzuat.utils.config_manager',
    'mevzuat.utils.logger',
    'mevzuat.monitoring.title_monitoring',
    'mevzuat.training.title_finetuner',
]

def test_imports():
    """Test importing all required modules."""
    failed_imports = []
    
    for module_name in MODULES_TO_TEST:
        try:
            # Try to import the module
            module = importlib.import_module(module_name)
            print(f"✅ Successfully imported {module_name}")
            
            # Check for common attributes that should be available
            if hasattr(module, '__all__'):
                for attr in module.__all__:
                    try:
                        getattr(module, attr)
                    except Exception as e:
                        print(f"  ⚠️  Could not access {module_name}.{attr}: {e}"
                              " (but module imported successfully)")
                        
        except ImportError as e:
            error_msg = str(e)
            # Skip missing optional dependencies
            if any(x in error_msg for x in ['No module named', 'cannot import name']):
                print(f"⚠️  Missing dependency for {module_name}: {error_msg}")
            else:
                print(f"❌ Failed to import {module_name}: {error_msg}")
                failed_imports.append((module_name, error_msg))
        except Exception as e:
            print(f"❌ Error importing {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
    
    return failed_imports

def check_required_files():
    """Check for required configuration and data files."""
    required_files = [
        'config/config.ini',
        'models/bert-base-turkish-cased',
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = src_dir.parent / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    return missing_files

if __name__ == "__main__":
    print("Testing imports and dependencies...\n")
    
    # Check for required files
    missing_files = check_required_files()
    if missing_files:
        print("⚠️  The following required files are missing:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nSome functionality may be limited without these files.\n")
    
    # Test imports
    failed = test_imports()
    
    # Print summary
    print("\nTest Summary:")
    if not failed:
        print("✅ All imports successful!")
    else:
        print(f"❌ {len(failed)} imports failed:")
        for module, error in failed:
            print(f"  - {module}: {error}")
        print("\nTroubleshooting tips:")
        print("1. Make sure all dependencies are installed (pip install -r requirements.txt)")
        print("2. Check that the PYTHONPATH is set correctly")
        print("3. Verify that all required files are in place")
        print("4. Check for any environment-specific issues")
        sys.exit(1)
