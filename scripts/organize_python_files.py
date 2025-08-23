import os
import shutil
from pathlib import Path

# Define source and target directories
src_dir = Path('/home/altay/Masaüstü/mevzuat/src')
mevzuat_dir = src_dir / 'mevzuat'

# Ensure target directories exist
(mevzuat_dir / 'ui/widgets').mkdir(parents=True, exist_ok=True)
(mevzuat_dir / 'core').mkdir(exist_ok=True)
(mevzuat_dir / 'models').mkdir(exist_ok=True)
(mevzuat_dir / 'services').mkdir(exist_ok=True)
(mevzuat_dir / 'utils').mkdir(exist_ok=True)
(mevzuat_dir / 'api').mkdir(exist_ok=True)

# File movement mapping
file_mapping = {
    # UI Files
    'app/ui/main_window.py': 'ui/',
    'app/ui/document_viewer.py': 'ui/',
    'app/ui/settings_dialog.py': 'ui/',
    'app/ui/document_preview.py': 'ui/widgets/',
    'app/ui/document_preview_widget.py': 'ui/widgets/',
    'app/ui/document_tree_widget.py': 'ui/widgets/',
    'app/ui/pdf_viewer_widget.py': 'ui/widgets/',
    'app/ui/result_widget.py': 'ui/widgets/',
    'app/ui/search_results_widget.py': 'ui/widgets/',
    'app/ui/search_widget.py': 'ui/widgets/',
    'app/ui/stats_widget.py': 'ui/widgets/',
    
    # Core functionality
    'app/core/app_manager.py': 'core/',
    'app/core/bert_title_analyzer.py': 'core/',
    'app/core/database_manager.py': 'core/',
    'app/core/document_processor.py': 'core/',
    'app/core/file_watcher.py': 'core/',
    'app/core/legal_analyzer.py': 'core/',
    'app/core/search_engine.py': 'core/',
    'app/core/semantic_search_alternative.py': 'core/',
    'app/core/tapu_kadastro.py': 'core/',
    'app/core/text_analyzer.py': 'core/',
    'app/core/turkish_bert.py': 'core/',
    'app/core/db_migrations/': 'core/db_migrations/',
    
    # Monitoring and training
    'app/monitoring/title_monitoring.py': 'monitoring/',
    'app/training/title_finetuner.py': 'training/',
    
    # Utils
    'app/utils/config_manager.py': 'utils/',
    'app/utils/document_classifier.py': 'utils/',
    'app/utils/logger.py': 'utils/',
    'app/utils/text_processor.py': 'utils/',
}

# Move files according to mapping
for src_pattern, target_dir in file_mapping.items():
    src_path = src_dir / src_pattern
    if src_path.is_dir():
        # Handle directory copies
        target_path = mevzuat_dir / target_dir
        os.makedirs(target_path, exist_ok=True)
        for item in src_path.glob('*'):
            if item.is_file():
                shutil.copy2(item, target_path / item.name)
                print(f"Copied {item} to {target_path}")
    elif src_path.exists():
        # Handle file moves
        target_path = mevzuat_dir / target_dir / src_path.name
        os.makedirs(mevzuat_dir / target_dir, exist_ok=True)
        shutil.move(str(src_path), str(target_path))
        print(f"Moved {src_path} to {target_path}")
    else:
        print(f"Warning: {src_path} not found")

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

remove_empty_dirs(src_dir / 'app')

print("\nPython file organization complete!")
print("Please update any import statements in the moved files to reflect the new structure.")
