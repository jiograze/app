"""
UI components for the Mevzuat Yönetim Sistemi.

This package contains all user interface components including windows, dialogs, and widgets.
"""

# Import main UI components for easier access
from .main_window import MainWindow
from .document_viewer import DocumentViewer
from .settings_dialog import SettingsDialog

__all__ = ['MainWindow', 'DocumentViewer', 'SettingsDialog', 'widgets']
