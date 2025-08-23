#!/usr/bin/env python3
"""Script to help locate the database file."""
import os
import sys
from pathlib import Path

def find_database():
    """Find the database file in common locations."""
    # Common locations to check
    search_paths = [
        "/home/altay/Masaüstü/mevzuat",
        "/home/altay/Masaüstü/mevzuat/mevzuat",
        "/home/altay/Masaüstü/mevzuat/mevzuat/MevzuatSistemi",
        "/home/altay/Masaüstü/mevzuat/C:\\Users\\klc\\Documents\\MevzuatDeposu/db",
    ]
    
    print("Searching for database file...")
    for path in search_paths:
        path = Path(path)
        if path.exists():
            print(f"\nContents of {path}:")
            try:
                for item in path.glob("**/*.sqlite"):
                    print(f"  - {item} (exists: {item.exists()}, size: {item.stat().st_size/1024/1024:.2f} MB)")
            except Exception as e:
                print(f"  Error reading {path}: {e}")
    
    print("\nTrying to list the database directory...")
    db_dir = "/home/altay/Masaüstü/mevzuat/C:\\Users\\klc\\Documents\\MevzuatDeposu/db"
    try:
        print(f"\nContents of {db_dir}:")
        for item in Path(db_dir).iterdir():
            print(f"  - {item.name} (size: {item.stat().st_size/1024/1024:.2f} MB)")
    except Exception as e:
        print(f"Error reading {db_dir}: {e}")

if __name__ == "__main__":
    find_database()
