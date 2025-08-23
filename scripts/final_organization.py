import os
import shutil
from pathlib import Path

# Define source and target directories
src_dir = Path('/home/altay/Masaüstü/mevzuat/src')
mevzuat_dir = src_dir / 'mevzuat'

# Ensure target directories exist
(mevzuat_dir / 'api').mkdir(exist_ok=True)
(mevzuat_dir / 'core').mkdir(exist_ok=True)
(mevzuat_dir / 'models').mkdir(exist_ok=True)
(mevzuat_dir / 'services').mkdir(exist_ok=True)
(mevzuat_dir / 'utils').mkdir(exist_ok=True)
(mevzuat_dir / 'web').mkdir(exist_ok=True)

# File movement mapping
file_mapping = {
    # Move core functionality
    'core/app_manager.py': 'core/app_manager.py',
    'core/bert_title_analyzer.py': 'core/bert_title_analyzer.py',
    'core/database_manager.py': 'core/database.py',
    'core/document_processor.py': 'core/processor.py',
    'core/file_watcher.py': 'core/watcher.py',
    'core/legal_analyzer.py': 'core/analyzer.py',
    'core/search_engine.py': 'core/search.py',
    'core/semantic_search_alternative.py': 'core/semantic.py',
    'core/tapu_kadastro.py': 'core/tapu.py',
    'core/text_analyzer.py': 'core/text_analyzer.py',
    'core/turkish_bert.py': 'core/bert.py',
    'core/db_migrations/': 'core/migrations/',
    
    # Move UI components
    'ui/': 'ui/',
    
    # Move monitoring
    'monitoring/': 'monitoring/',
    
    # Move training
    'training/': 'training/',
    
    # Move web components
    'web/': 'web/'
}

# Move files according to mapping
for src, dst in file_mapping.items():
    src_path = mevzuat_dir / src
    dst_path = mevzuat_dir / dst
    
    if src.endswith('/'):  # Handle directories
        os.makedirs(dst_path, exist_ok=True)
        for item in src_path.glob('*'):
            if item.is_file() and item.suffix == '.py':
                shutil.move(str(item), str(dst_path / item.name))
                print(f"Moved {item} to {dst_path}")
    else:  # Handle individual files
        if src_path.exists():
            os.makedirs(dst_path.parent, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            print(f"Moved {src_path} to {dst_path}")

# Clean up empty directories
def remove_empty_dirs(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            try:
                os.removedirs(dir_path)
                print(f"Removed empty directory: {dir_path}")
            except OSError:
                pass

remove_empty_dirs(mevzuat_dir)

print("\nFile organization complete!")
