from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mevzuat',
    version='0.1.0',
    description='Mevzuat Yönetim Sistemi - A comprehensive legal document management system',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/mevzuat',
    packages=find_packages(include=['mevzuat*']),
    include_package_data=True,
    install_requires=open('requirements/base.txt').read().splitlines(),
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Legal Industry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    entry_points={
        'console_scripts': [
            'mevzuat=mevzuat.cli:main',
        ],
    },
)
