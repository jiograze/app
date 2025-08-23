"""
Search Results Widget - Combines search results list with document preview
"""

import logging
from typing import List, Dict, Optional, Any

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListView, QLabel, QFrame, 
    QAbstractItemView, QSplitter, QToolBar, QAction, QMenu, QSizePolicy
)

from .document_preview import DocumentPreview
from mevzuat.core.database_manager import DatabaseManager

class SearchResultsWidget(QWidget):
    """Widget that combines search results list with document preview"""
    
    # Signals
    document_opened = pyqtSignal(dict)  # Emitted when a document is opened in full view
    
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db
        self.current_results = []
        self.current_query = ""
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Search results list
        self.results_list = self.create_results_list()
        self.splitter.addWidget(self.results_list)
        
        # Right panel - Document preview
        self.document_preview = DocumentPreview(self.db)
        self.splitter.addWidget(self.document_preview)
        
        # Set initial splitter sizes (40% results, 60% preview)
        self.splitter.setSizes([400, 600])
        
        # Add splitter to main layout
        layout.addWidget(self.splitter)
        
        # Set minimum size
        self.setMinimumSize(800, 400)
    
    def create_results_list(self) -> QWidget:
        """Create the search results list widget"""
        # Container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        self.sort_action = QAction("Sırala", self)
        self.sort_action.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_ArrowDown')))
        self.sort_menu = QMenu()
        self.sort_menu.addAction("En İyi Eşleşme").setData("relevance")
        self.sort_menu.addAction("Tarihe Göre (Yeniden Eskiye)").setData("date_desc")
        self.sort_menu.addAction("Tarihe Göre (Eskiden Yeniye)").setData("date_asc")
        self.sort_menu.addAction("Başlığa Göre (A-Z)").setData("title_asc")
        self.sort_menu.addAction("Başlığa Göre (Z-A)").setData("title_desc")
        self.sort_action.setMenu(self.sort_menu)
        
        toolbar.addAction(self.sort_action)
        
        # Results count label
        self.results_count = QLabel("0 sonuç")
        self.results_count.setStyleSheet("padding: 5px;")
        
        # Add to layout
        layout.addWidget(toolbar)
        
        # Add a line separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        layout.addWidget(self.results_count)
        
        # List view for search results
        self.results_view = QListView()
        self.results_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_view.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Set item delegate for custom item rendering if needed
        # self.results_view.setItemDelegate(CustomItemDelegate())
        
        # Set model
        self.results_model = QStandardItemModel()
        self.results_view.setModel(self.results_model)
        
        # Add to layout
        layout.addWidget(self.results_view)
        
        return container
    
    def setup_connections(self):
        """Setup signal connections"""
        # Connect selection changed
        self.results_view.selectionModel().currentChanged.connect(self.on_result_selected)
        
        # Connect sort menu
        self.sort_menu.triggered.connect(self.on_sort_triggered)
        
        # Connect document preview signals
        self.document_preview.document_opened.connect(self.document_opened)
        
        # Connect context menu
        self.results_view.customContextMenuRequested.connect(self.show_context_menu)
    
    def set_search_results(self, query: str, results: List[Dict[str, Any]]):
        """Set the search results to display"""
        self.current_query = query
        self.current_results = results
        
        # Update results count
        count = len(results)
        self.results_count.setText(f"{count} sonuç")
        
        # Clear existing items
        self.results_model.clear()
        
        # Add results to the model
        for result in results:
            item = QStandardItem()
            
            # Format the item text with HTML for rich text display
            title = result.get('title', 'Başlıksız Belge')
            doc_type = result.get('document_type', '')
            date = result.get('publication_date', '')
            
            # Highlight query terms in title
            highlighted_title = self.highlight_text(title, query)
            
            # Build item text with HTML formatting
            item_text = f"<b>{highlighted_title}</b>"
            
            if doc_type:
                item_text += f"<br><span style='color: #666;'>{doc_type}</span>"
                
            if date:
                item_text += f"<br><span style='color: #666;'>{date}</span>"
            
            # Set item data
            item.setText(item_text)
            item.setData(result, Qt.UserRole)  # Store full result data
            item.setToolTip(title)
            
            self.results_model.appendRow(item)
        
        # Select first item if available
        if self.results_model.rowCount() > 0:
            first_index = self.results_model.index(0, 0)
            self.results_view.setCurrentIndex(first_index)
            self.on_result_selected(first_index, None)
    
    def highlight_text(self, text: str, query: str) -> str:
        """Highlight query terms in the text"""
        if not text or not query:
            return text
            
        # Simple case-insensitive highlighting
        import re
        query_terms = re.findall(r'\b\w+\b', query, re.UNICODE)
        
        if not query_terms:
            return text
            
        # Create a case-insensitive regex pattern
        pattern = '|'.join(map(re.escape, query_terms))
        
        try:
            # Use regex to find all matches (case insensitive)
            highlighted = re.sub(
                f'({pattern})', 
                r'<span style="background-color: #fffbcc;">\1</span>', 
                text, 
                flags=re.IGNORECASE | re.UNICODE
            )
            return highlighted
        except Exception as e:
            self.logger.warning(f"Highlighting error: {e}")
            return text
    
    def on_result_selected(self, current: QModelIndex, previous: QModelIndex = None):
        """Handle selection of a search result"""
        try:
            if not current.isValid():
                self.document_preview.clear()
                return
                
            item = self.results_model.itemFromIndex(current)
            if not item:
                self.document_preview.clear()
                return
                
            # Get the full result data
            result_data = item.data(Qt.UserRole)
            if not result_data:
                self.document_preview.clear()
                return
            
            # Show loading state
            self.document_preview.show_loading("Belge yükleniyor...")
            
            # Get the document details from the database
            doc_id = result_data.get('id')
            if doc_id:
                # Try to get the document with full details
                document = self.db.get_document(doc_id)
                if document:
                    # Convert to dict if it's a model instance
                    if not isinstance(document, dict):
                        document = {
                            'id': document.id,
                            'title': document.title,
                            'document_type': document.document_type,
                            'law_number': document.law_number,
                            'publication_date': document.publication_date,
                            'effective_date': document.effective_date,
                            'file_path': document.file_path,
                            'content': result_data.get('content', '')
                        }
                    
                    # Get articles if available
                    articles = self.db.get_articles_for_document(doc_id)
                    article_data = None
                    
                    # If this result is for a specific article, find it
                    article_id = result_data.get('article_id')
                    if article_id and articles:
                        for article in articles:
                            if str(article.id) == str(article_id) or article.article_number == article_id:
                                article_data = {
                                    'id': article.id,
                                    'article_number': article.article_number,
                                    'title': article.title,
                                    'content': article.content,
                                    'is_repealed': article.is_repealed,
                                    'is_amended': article.is_amended
                                }
                                break
                    
                    # Show the document in the preview panel
                    self.document_preview.show_document(document, article_data)
                    return
            
            # Fallback to showing just the result data
            self.document_preview.show_document(result_data)
            
        except Exception as e:
            self.logger.error(f"Belge yükleme hatası: {e}")
            self.document_preview.show_document({
                'title': 'Hata',
                'content': f'Belge yüklenirken bir hata oluştu: {str(e)}'
            })
    
    def on_sort_triggered(self, action):
        """Handle sort menu actions"""
        sort_key = action.data()
        self.logger.info(f"Sorting by: {sort_key}")
        
        if not self.current_results:
            return
            
        # Sort the results
        if sort_key == "relevance":
            # Already sorted by relevance
            pass
        elif sort_key == "date_desc":
            self.current_results.sort(
                key=lambda x: x.get('publication_date', ''), 
                reverse=True
            )
        elif sort_key == "date_asc":
            self.current_results.sort(
                key=lambda x: x.get('publication_date', ''), 
                reverse=False
            )
        elif sort_key == "title_asc":
            self.current_results.sort(
                key=lambda x: x.get('title', '').lower()
            )
        elif sort_key == "title_desc":
            self.current_results.sort(
                key=lambda x: x.get('title', '').lower(), 
                reverse=True
            )
        
        # Update the view
        self.set_search_results(self.current_query, self.current_results)
    
    def show_context_menu(self, position):
        """Show context menu for search result items"""
        index = self.results_view.indexAt(position)
        if not index.isValid():
            return
            
        item = self.results_model.itemFromIndex(index)
        if not item:
            return
            
        result_data = item.data(Qt.UserRole)
        if not result_data:
            return
            
        menu = QMenu()
        
        open_action = menu.addAction("Belgeyi Aç")
        open_new_tab_action = menu.addAction("Yeni Sekmede Aç")
        menu.addSeparator()
        copy_title_action = menu.addAction("Başlığı Kopyala")
        copy_reference_action = menu.addAction("Referansı Kopyala")
        
        action = menu.exec_(self.results_view.viewport().mapToGlobal(position))
        
        if action == open_action:
            self.document_opened.emit(result_data)
        elif action == open_new_tab_action:
            # Emit with a flag to open in new tab if supported by parent
            self.document_opened.emit({"document": result_data, "new_tab": True})
        elif action == copy_title_action:
            clipboard = QApplication.clipboard()
            clipboard.setText(result_data.get('title', ''))
        elif action == copy_reference_action:
            # Format a reference string
            ref = self.format_reference(result_data)
            if ref:
                clipboard = QApplication.clipboard()
                clipboard.setText(ref)
    
    def format_reference(self, result_data: Dict[str, Any]) -> str:
        """Format a reference string for the document"""
        parts = []
        
        title = result_data.get('title')
        if title:
            parts.append(f'"{title}"')
            
        doc_type = result_data.get('document_type')
        if doc_type:
            parts.append(doc_type)
            
        law_number = result_data.get('law_number')
        if law_number:
            parts.append(f'Sayı: {law_number}')
            
        date = result_data.get('publication_date')
        if date:
            parts.append(f'({date})')
            
        return ' '.join(parts)
    
    def clear(self):
        """Clear the search results and preview"""
        self.current_query = ""
        self.current_results = []
        self.results_model.clear()
        self.results_count.setText("0 sonuç")
        self.document_preview.clear()
