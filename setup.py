from setuptools import setup, find_packages
import os
from pathlib import Path

def read_requirements(file_name):
    """Read requirements from a file."""
    requirements = []
    file_path = Path(__file__).parent / 'requirements' / file_name
    
    if not file_path.exists():
        return requirements
        
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Handle -r includes
            if line.startswith('-r '):
                included_file = line[3:].strip()
                requirements.extend(read_requirements(included_file))
            else:
                requirements.append(line)
    return requirements

def read_readme():
    """Read the README file."""
    readme_path = Path(__file__).parent / 'README.md'
    try:
        return readme_path.read_text(encoding='utf-8')
    except Exception:
        return "Mevzuat Yönetim Sistemi - Legal Document Management System"

# Read base requirements
install_requires = read_requirements('base.txt')
extras_require = {
    'dev': read_requirements('dev.txt'),
    'test': [
        'pytest>=7.0.0',
        'pytest-cov>=4.0.0',
        'pytest-mock>=3.10.0',
        'pytest-xdist>=3.0.0',
        'coverage>=7.0.0',
        'factory-boy>=3.0.0',
        'Faker>=18.0.0',
    ],
    'docs': [
        'Sphinx>=7.0.0',
        'sphinx-rtd-theme>=1.0.0',
        'sphinx-autodoc-typehints>=1.0.0',
    ],
}

# All extras include everything
extras_require['all'] = list(set(req for reqs in extras_require.values() for req in reqs))

setup(
    name="mevzuat",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "mevzuat": ["py.typed", "*.pyi"],
    },
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires='>=3.8',
    
    # Metadata
    author="Mevzuat Ekibi",
    author_email="mevzuat@example.com",
    description="Mevzuat Yönetim Sistemi - Legal Document Management System",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mevzuat",
    
    # Entry points
    entry_points={
        'console_scripts': [
            'mevzuat=mevzuat.cli:main',
        ],
        'flask.commands': [
            'init-db=mevzuat.commands:init_db',
            'create-admin=mevzuat.commands:create_admin',
        ],
    },
    
    # Project classification
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Legal Industry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Flask',
        'Topic :: Office/Business :: Legal',
        'Operating System :: OS Independent',
        'Natural Language :: Turkish',
        'Typing :: Typed',
    ],
    
    # Additional metadata
    keywords='legal document management mevzuat',
    project_urls={
        'Documentation': 'https://github.com/yourusername/mevzuat/docs',
        'Source': 'https://github.com/yourusername/mevzuat',
        'Tracker': 'https://github.com/yourusername/mevzuat/issues',
        'Changelog': 'https://github.com/yourusername/mevzuat/blob/main/CHANGELOG.md',
    },
    
    # Additional metadata for PyPI
    license='MIT',
    platforms=['any'],
    zip_safe=False,
)
