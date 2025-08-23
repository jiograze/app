"""
Custom widgets for the Mevzuat Yönetim Sistemi UI.

This module contains reusable UI components and widgets.
"""

# Import widgets for easier access
from .document_preview import DocumentPreview
from .document_preview_widget import DocumentPreviewWidget
from .document_tree_widget import DocumentTreeWidget
from .pdf_viewer_widget import PdfViewerWidget
from .result_widget import ResultWidget
from .search_results_widget import SearchResultsWidget
from .search_widget import SearchWidget
from .stats_widget import StatsWidget

__all__ = [
    'DocumentPreview',
    'DocumentPreviewWidget',
    'DocumentTreeWidget',
    'PdfViewerWidget',
    'ResultWidget',
    'SearchResultsWidget',
    'SearchWidget',
    'StatsWidget'
]
