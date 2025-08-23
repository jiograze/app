#!/usr/bin/env python
"""
Test script - uygulama hatalarını debug etmek için
"""

import os
import sys
from pathlib import Path

print("=== Mevzuat Sistemi Test ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Script directory: {Path(__file__).parent}")

# Proje kökünü path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Python path: {sys.path[:3]}")  # İlk 3 path

try:
    print("PyQt5 import test...")
    from PyQt5.QtWidgets import QApplication

    print("✓ PyQt5 imported successfully")

    print("Config manager import test...")
    from app.utils.config_manager import ConfigManager

    print("✓ ConfigManager imported successfully")

    print("Logger import test...")
    from app.utils.logger import setup_logger

    print("✓ Logger imported successfully")

    print("Database manager import test...")
    from app.core.database_manager import DatabaseManager

    print("✓ DatabaseManager imported successfully")

    print("File watcher import test...")
    from app.core.file_watcher import FileWatcher

    print("✓ FileWatcher imported successfully")

    print("Document processor import test...")
    from app.core.document_processor import DocumentProcessor

    print("✓ DocumentProcessor imported successfully")

    print("Search engine import test...")
    from app.core.search_engine import SearchEngine

    print("✓ SearchEngine imported successfully")

    print("Main window import test...")
    from app.ui.main_window import MainWindow

    print("✓ MainWindow imported successfully")

    print("App manager import test...")
    from app.core.app_manager import MevzuatApp

    print("✓ MevzuatApp imported successfully")

    print("\n=== All imports successful! ===")
    print("Test completed successfully!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
