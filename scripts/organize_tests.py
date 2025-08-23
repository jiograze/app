import os
import shutil
from pathlib import Path

# Define source and target directories
src_dir = Path('/home/altay/Masaüstü/mevzuat/src')
tests_dir = Path('/home/altay/Masaüstü/mevzuat/tests')

# Map test files to their target directories
test_mapping = {
    # Unit tests (testing individual components in isolation)
    'test_bert_title_analyzer.py': 'unit/',
    'test_tapu_analyzer.py': 'unit/',
    'test_bert_integration.py': 'unit/',
    
    # Integration tests (testing interaction between components)
    'test_ui_core_connection.py': 'integration/',
    'test_semantic_search.py': 'integration/',
    'test_document_viewer.py': 'integration/',
    
    # Functional tests (end-to-end testing)
    'test_belge_ekleme.py': 'functional/',
    'test_eksik_kontrol.py': 'functional/',
    'test_file_organization.py': 'functional/',
    'test_improved_indexing.py': 'functional/',
    
    # Test utilities and fixtures
    'test_env.py': 'fixtures/',
    'test_ocr_module.py': 'fixtures/',
    'test_fts_check.py': 'fixtures/',
}

# Create a reverse mapping for verification
reverse_mapping = {}
for test_file, target_dir in test_mapping.items():
    reverse_mapping[target_dir + test_file] = src_dir / test_file

# Move the files
for test_file, target_dir in test_mapping.items():
    src_path = src_dir / test_file
    target_path = tests_dir / target_dir / test_file
    
    # Handle test files in src/tests directory
    if not src_path.exists() and (src_dir / 'tests' / test_file).exists():
        src_path = src_dir / 'tests' / test_file
    
    if src_path.exists():
        # Create target directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Move the file
        shutil.move(str(src_path), str(target_path))
        print(f"Moved {src_path} to {target_path}")
    else:
        print(f"Warning: {test_file} not found in expected locations")

print("Test file organization complete!")
