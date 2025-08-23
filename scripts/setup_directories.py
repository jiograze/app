import os
from pathlib import Path

def create_directory_structure(base_path):
    """Create the directory structure for the project."""
    # Main directories
    directories = [
        'core',
        'core/migrations',
        'ui',
        'ui/widgets',
        'models',
        'services',
        'utils',
        'monitoring',
        'training',
        'api',
        'web',
        'tests',
        'tests/unit',
        'tests/integration',
        'tests/functional',
        'tests/fixtures'
    ]
    
    # Create requirements directory first
    requirements_dir = Path(base_path).parent / 'requirements'
    requirements_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {requirements_dir}")
    
    # Create each directory
    for directory in directories:
        dir_path = Path(base_path) / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
        
        # Create __init__.py in each directory
        init_file = dir_path / '__init__.py'
        if not init_file.exists():
            init_file.touch()
            print(f"  - Created {init_file}")
    
    # Create additional required files
    required_files = {
        'README.md': "# Mevzuat Yönetim Sistemi\n\nDocumentation coming soon..."
    }
    
    # Requirements files in the project root
    requirements_files = {
        'requirements.txt': "# Core dependencies\n-r requirements/base.txt\n\n# Development dependencies\n-r requirements/dev.txt\n\n# Test dependencies\n-r requirements/test.txt",
        'requirements/base.txt': "# Core dependencies\nflask>=2.0.0\nsqlalchemy>=1.4.0\npandas>=1.3.0\nnumpy>=1.21.0\ntransformers>=4.11.0\ntorch>=1.9.0\nPyQt5>=5.15.0\npdf2image>=1.16.0\npython-dotenv>=0.19.0\nrequests>=2.26.0",
        'requirements/dev.txt': "# Development dependencies\npylint>=2.11.0\nblack>=21.9b0\nisort>=5.9.3\nmypy>=0.910\npre-commit>=2.15.0\npytest>=6.2.5\npytest-cov>=2.12.0",
        'requirements/test.txt': "# Test dependencies\npytest>=6.2.5\npytest-cov>=2.12.0\npytest-mock>=3.6.1\ncoverage>=6.1.2"
    }
    
    # Create regular files in the package
    for filename, content in required_files.items():
        file_path = Path(base_path) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created file: {file_path}")
    
    # Create requirements files in the project root
    for filename, content in requirements_files.items():
        file_path = Path(base_path).parent.parent / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created file: {file_path}")

if __name__ == "__main__":
    # Create directory structure in the src/mevzuat directory
    create_directory_structure('/home/altay/Masaüstü/mevzuat/src/mevzuat')
    print("\nDirectory structure setup complete!")
