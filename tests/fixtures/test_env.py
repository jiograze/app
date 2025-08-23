import sys
import os
from pathlib import Path

print("Python version:", sys.version)
print("\nPython path:")
for p in sys.path:
    print(f"  - {p}")

print("\nCurrent working directory:", os.getcwd())
print("\nFiles in current directory:")
for f in Path('.').iterdir():
    print(f"  - {f.name}")

print("\nTrying to import spaCy...")
try:
    import spacy
    print("Successfully imported spaCy")
    print(f"spaCy version: {spacy.__version__}")
    
    print("\nTrying to load Turkish model...")
    try:
        nlp = spacy.load("tr_core_news_md")
        print("Successfully loaded Turkish model")
    except Exception as e:
        print(f"Error loading Turkish model: {str(e)}")
        print("You may need to run: python -m spacy download tr_core_news_md")
        
except ImportError:
    print("spaCy is not installed. Please install it with: pip install spacy")
