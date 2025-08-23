import os
from pathlib import Path

# Define source directory
src_dir = Path('/home/altay/Masaüstü/mevzuat/src/mevzuat')

# Define target structure
target_structure = {
    'core/': {
        'description': 'Core application logic and business rules',
        'files': [
            'app_manager.py',
            'database.py',
            'search.py',
            'watcher.py',
            'analyzer.py',
            'processor.py',
            'semantic.py',
            'bert.py',
            'bert_title_analyzer.py',
            'tapu.py',
            'text_analyzer.py',
            'migrations/'
        ]
    },
    'ui/': {
        'description': 'User interface components',
        'files': [
            'main_window.py',
            'settings_dialog.py',
            'document_viewer.py',
            'widgets/'
        ]
    },
    'models/': {
        'description': 'Data models and database schemas',
        'files': ['__init__.py']
    },
    'services/': {
        'description': 'Business logic services',
        'files': ['__init__.py']
    },
    'utils/': {
        'description': 'Utility functions and helpers',
        'files': [
            'config_manager.py',
            'document_classifier.py',
            'logger.py',
            'text_processor.py'
        ]
    },
    'monitoring/': {
        'description': 'Monitoring and observability tools',
        'files': ['title_monitoring.py']
    },
    'training/': {
        'description': 'Model training code',
        'files': ['title_finetuner.py']
    },
    'api/': {
        'description': 'API endpoints and routes',
        'files': ['__init__.py']
    },
    'web/': {
        'description': 'Web interface components',
        'files': ['__init__.py']
    },
    'tests/': {
        'description': 'Test files',
        'files': []
    }
}

def analyze_files():
    """Analyze Python files in the source directory."""
    python_files = list(src_dir.rglob('*.py'))
    file_info = []
    
    for file_path in python_files:
        # Skip __pycache__ and virtual environment files
        if '__pycache__' in str(file_path) or '.venv' in str(file_path):
            continue
            
        rel_path = file_path.relative_to(src_dir)
        file_info.append({
            'path': str(rel_path),
            'size': file_path.stat().st_size,
            'lines': sum(1 for _ in file_path.open('r', encoding='utf-8')),
            'type': _get_file_type(str(rel_path))
        })
    
    return file_info

def _get_file_type(file_path):
    """Determine the type of file based on its path."""
    if 'widgets' in file_path:
        return 'ui_widget'
    elif 'core' in file_path:
        return 'core_module'
    elif 'utils' in file_path:
        return 'utility'
    elif 'ui/' in file_path:
        return 'ui_component'
    elif 'tests/' in file_path:
        return 'test'
    elif 'migrations/' in file_path:
        return 'migration'
    elif 'models/' in file_path:
        return 'model'
    elif 'services/' in file_path:
        return 'service'
    elif 'monitoring/' in file_path:
        return 'monitoring'
    elif 'training/' in file_path:
        return 'training'
    elif 'api/' in file_path:
        return 'api'
    elif 'web/' in file_path:
        return 'web'
    return 'other'

def create_mapping():
    """Create a mapping of current files to their target locations."""
    mapping = {}
    
    # Core files
    mapping.update({
        str(src_dir / 'core' / 'app_manager.py'): str(src_dir / 'core' / 'app_manager.py'),
        str(src_dir / 'core' / 'database.py'): str(src_dir / 'core' / 'database.py'),
        str(src_dir / 'core' / 'search.py'): str(src_dir / 'core' / 'search.py'),
        # Add other core files...
    })
    
    # UI files
    mapping.update({
        str(src_dir / 'ui' / 'main_window.py'): str(src_dir / 'ui' / 'main_window.py'),
        str(src_dir / 'ui' / 'settings_dialog.py'): str(src_dir / 'ui' / 'settings_dialog.py'),
        str(src_dir / 'ui' / 'document_viewer.py'): str(src_dir / 'ui' / 'document_viewer.py'),
        # Add other UI files...
    })
    
    # Widgets
    for widget in (src_dir / 'ui' / 'widgets').glob('*.py'):
        mapping[str(widget)] = str(widget)
    
    # Utils
    for util in (src_dir / 'utils').glob('*.py'):
        mapping[str(util)] = str(util)
    
    # Other directories
    for subdir in ['monitoring', 'training', 'api', 'web']:
        dir_path = src_dir / subdir
        if dir_path.exists():
            for file_path in dir_path.glob('*.py'):
                mapping[str(file_path)] = str(file_path)
    
    return mapping

def generate_structure_docs():
    """Generate documentation for the project structure."""
    docs = "# Project Structure\n\n"
    
    for dir_name, dir_info in target_structure.items():
        docs += f"## {dir_name}\n"
        docs += f"{dir_info['description']}\n\n"
        
        if dir_info['files']:
            docs += "### Files\n"
            for file in dir_info['files']:
                if file.endswith('/'):  # It's a directory
                    docs += f"- `{dir_name}{file}`: Contains related files\n"
                else:
                    docs += f"- `{file}`\n"
        docs += "\n"
    
    return docs

if __name__ == "__main__":
    # Analyze files
    files = analyze_files()
    print(f"Found {len(files)} Python files")
    
    # Create mapping
    mapping = create_mapping()
    print(f"Created mapping for {len(mapping)} files")
    
    # Generate structure documentation
    structure_docs = generate_structure_docs()
    with open(src_dir.parent / 'PROJECT_STRUCTURE.md', 'w', encoding='utf-8') as f:
        f.write(structure_docs)
    
    print("Project structure documentation generated at PROJECT_STRUCTURE.md")
