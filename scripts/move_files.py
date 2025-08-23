import os
import shutil
from pathlib import Path

def move_files():
    """Move files to their new locations based on the analysis."""
    base_src = Path('/home/altay/Masaüstü/mevzuat/src/mevzuat')
    base_dst = base_src  # Same base directory
    
    # Define file mappings: source -> destination
    file_mappings = {
        # Core files
        'core/app_manager.py': 'core/app_manager.py',
        'core/database.py': 'core/database.py',
        'core/search.py': 'core/search.py',
        'core/watcher.py': 'core/watcher.py',
        'core/analyzer.py': 'core/analyzer.py',
        'core/processor.py': 'core/processor.py',
        'core/semantic.py': 'core/semantic.py',
        'core/bert.py': 'core/bert.py',
        'core/bert_title_analyzer.py': 'core/bert_title_analyzer.py',
        'core/tapu.py': 'core/tapu.py',
        'core/text_analyzer.py': 'core/text_analyzer.py',
        'core/migrations/': 'core/migrations/',
        
        # UI files
        'ui/main_window.py': 'ui/main_window.py',
        'ui/settings_dialog.py': 'ui/settings_dialog.py',
        'ui/document_viewer.py': 'ui/document_viewer.py',
        'ui/widgets/result_widget.py': 'ui/widgets/result_widget.py',
        'ui/widgets/document_preview_widget.py': 'ui/widgets/document_preview_widget.py',
        'ui/widgets/pdf_viewer_widget.py': 'ui/widgets/pdf_viewer_widget.py',
        'ui/widgets/search_widget.py': 'ui/widgets/search_widget.py',
        'ui/widgets/document_tree_widget.py': 'ui/widgets/document_tree_widget.py',
        'ui/widgets/stats_widget.py': 'ui/widgets/stats_widget.py',
        'ui/widgets/search_results_widget.py': 'ui/widgets/search_results_widget.py',
        'ui/widgets/document_preview.py': 'ui/widgets/document_preview.py',
        
        # Utils
        'utils/config_manager.py': 'utils/config_manager.py',
        'utils/document_classifier.py': 'utils/document_classifier.py',
        'utils/logger.py': 'utils/logger.py',
        'utils/text_processor.py': 'utils/text_processor.py',
        
        # Monitoring
        'monitoring/title_monitoring.py': 'monitoring/title_monitoring.py',
        
        # Training
        'training/title_finetuner.py': 'training/title_finetuner.py',
    }
    
    # Create a reverse mapping to check for duplicates
    dest_files = set()
    for src, dst in file_mappings.items():
        if dst in dest_files:
            print(f"Warning: Duplicate destination detected: {dst}")
        dest_files.add(dst)
    
    # Move files
    for src_rel, dst_rel in file_mappings.items():
        src = base_src / src_rel
        dst = base_dst / dst_rel
        
        # Skip if source doesn't exist
        if not src.exists():
            print(f"Source file not found: {src}")
            continue
            
        # Create destination directory if it doesn't exist
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Move the file
        try:
            if src.is_file():
                shutil.move(str(src), str(dst))
                print(f"Moved: {src} -> {dst}")
            elif src.is_dir():
                # For directories, move each file individually
                for file in src.glob('**/*'):
                    if file.is_file():
                        rel_path = file.relative_to(src)
                        dest_file = dst / rel_path
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file), str(dest_file))
                        print(f"Moved: {file} -> {dest_file}")
                # Remove empty source directory
                try:
                    src.rmdir()
                    print(f"Removed empty directory: {src}")
                except OSError:
                    print(f"Could not remove directory (may not be empty): {src}")
        except Exception as e:
            print(f"Error moving {src} to {dst}: {e}")
    
    # Clean up empty directories
    for root, dirs, _ in os.walk(base_src, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                dir_path.rmdir()
                print(f"Removed empty directory: {dir_path}")
            except OSError:
                # Directory not empty, which is fine
                pass

def update_imports():
    """Update import statements in Python files to reflect the new structure."""
    base_dir = Path('/home/altay/Masaüstü/mevzuat/src/mevzuat')
    
    # Define import mappings: old_import -> new_import
    import_mappings = {
        'from core.': 'from mevzuat.core.',
        'from ui.': 'from mevzuat.ui.',
        'from utils.': 'from mevzuat.utils.',
        'from monitoring.': 'from mevzuat.monitoring.',
        'from training.': 'from mevzuat.training.',
        'import core.': 'import mevzuat.core.',
        'import ui.': 'import mevzuat.ui.',
        'import utils.': 'import mevzuat.utils.',
        'import monitoring.': 'import mevzuat.monitoring.',
        'import training.': 'import mevzuat.training.',
    }
    
    # Process all Python files
    for py_file in base_dir.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            updated = False
            for old_import, new_import in import_mappings.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    updated = True
            
            if updated:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated imports in: {py_file}")
                
        except Exception as e:
            print(f"Error processing {py_file}: {e}")

if __name__ == "__main__":
    print("Moving files to their new locations...")
    move_files()
    
    print("\nUpdating import statements...")
    update_imports()
    
    print("\nFile reorganization complete!")
