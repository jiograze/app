"""
Document Preview Panel - Shows a preview of the selected document in search results
"""

import logging
from typing import Optional, Dict, List

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import (
    QTextDocument, QTextCursor, QTextCharFormat, QFont, QTextFormat, 
    QColor, QTextBlockFormat, QTextLength, QPixmap, QIcon
)
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QScrollArea, 
    QFrame, QToolBar, QAction, QSizePolicy, QPushButton, QSplitter
)

from mevzuat.core.database_manager import DatabaseManager
from .document_viewer import DocumentViewer

class DocumentPreview(QWidget):
    """Document preview panel for search results"""
    
    # Signals
    document_opened = pyqtSignal(dict)  # Emitted when a document is opened in full view
    
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db
        self.current_document = None
        self.current_article = None
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        self.header = QWidget()
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        self.title_label = QLabel("Belge Önizleme")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        self.open_full_btn = QPushButton("Tam Ekran Aç")
        self.open_full_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_ArrowRight')))
        self.open_full_btn.setStyleSheet("font-size: 11px; padding: 2px 5px;")
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.open_full_btn)
        
        # Content area
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.content.setFrameStyle(QFrame.NoFrame)
        self.content.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set a minimum height for better visibility
        self.content.setMinimumHeight(200)
        
        # Add to main layout
        layout.addWidget(self.header)
        
        # Add a line separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        layout.addWidget(self.content)
        
        # Set default message
        self.content.setHtml(
            "<div style='color: #666; font-style: italic; text-align: center; margin-top: 50px;'>"
            "Bir belge seçin veya arama yapın..."
            "</div>"
        )
    
    def setup_connections(self):
        """Setup signal connections"""
        self.open_full_btn.clicked.connect(self.open_document_full)
    
    def show_document(self, document_data: Dict, article_data: Optional[Dict] = None):
        """Show document preview with enhanced formatting and error handling"""
        try:
            self.current_document = document_data
            self.current_article = article_data
            
            # Update title
            title = document_data.get('title', 'Başlıksız Belge')
            doc_type = document_data.get('document_type', '')
            
            # Set window title
            if doc_type:
                self.title_label.setText(f"{doc_type}: {title}")
            else:
                self.title_label.setText(title)
            
            # Start building the HTML content
            content = ['<div style="font-family: Arial, sans-serif; color: #333;">']
            
            # Add document metadata in a clean, readable format
            content.append(f'<h3 style="color: #2c3e50; margin-bottom: 10px;">{title}</h3>')
            
            # Metadata section
            metadata = []
            if doc_type:
                metadata.append(f'<b>Tür:</b> {doc_type}')
            if document_data.get('law_number'):
                metadata.append(f'<b>Sayı:</b> {document_data["law_number"]}')
            if document_data.get('publication_date'):
                metadata.append(f'<b>Yayım Tarihi:</b> {document_data["publication_date"]}')
            if document_data.get('effective_date'):
                metadata.append(f'<b>Yürürlük Tarihi:</b> {document_data["effective_date"]}')
            
            if metadata:
                content.append(
                    '<div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; '
                    'margin-bottom: 15px; border-left: 4px solid #3498db;">' +
                    ' • '.join(metadata) + 
                    '</div>'
                )
            
            # Add article content if available
            if article_data:
                content.append('<hr style="border: 0; border-top: 1px solid #eee; margin: 15px 0;">')
                
                article_title = article_data.get('title', '')
                article_number = article_data.get('article_number', '')
                
                # Format article header
                article_header = []
                if article_number:
                    article_header.append(f'Madde {article_number}')
                if article_title:
                    article_header.append(article_title)
                
                if article_header:
                    content.append(f'<h4 style="color: #2980b9; margin: 10px 0 5px 0;">{" - ".join(article_header)}</h4>')
                
                # Add article content with better formatting
                article_content = article_data.get('content', '')
                if article_content:
                    # Preserve paragraphs and basic formatting
                    formatted_content = article_content.replace('\n\n', '</p><p style="margin: 5px 0; line-height: 1.5;">')
                    formatted_content = formatted_content.replace('\n', '<br>')
                    content.append(f'<div style="margin: 10px 0; line-height: 1.6;"><p style="margin: 5px 0; line-height: 1.5;">{formatted_content}</p></div>')
                
                # Add article status indicators
                status = []
                if article_data.get('is_repealed'):
                    status.append('<span style="color: #e74c3c; font-weight: bold;">YÜRÜRLÜKTEN KALDIRILMIŞ</span>')
                if article_data.get('is_amended'):
                    status.append('<span style="color: #f39c12;">Değişiklik yapılmış</span>')
                
                if status:
                    content.append(
                        '<div style="margin-top: 10px; padding: 8px; background-color: #fef9e7; '
                        'border-radius: 4px; border-left: 3px solid #f1c40f;">' +
                        ' • '.join(status) +
                        '</div>'
                    )
            
            # Close the content div
            content.append('</div>')
            
            # Set the content with proper HTML structure
            self.content.setHtml(''.join(content))
            
            # Scroll to top
            self.content.verticalScrollBar().setValue(0)
            
            # Enable the open full button
            self.open_full_btn.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Belge önizleme hatası: {e}", exc_info=True)
            self.content.setHtml(
                "<div style='color: #e74c3c; text-align: center; margin: 50px 20px; padding: 20px; "
                "background-color: #fde8e8; border-radius: 4px; border-left: 4px solid #e74c3c;'>"
                "<h4 style='margin-top: 0;'>Belge yüklenirken bir hata oluştu</h4>"
                f"<p style='color: #7f8c8d;'>{str(e)}</p>"
                "<p>Lütfen daha sonra tekrar deneyin veya yöneticiye başvurun.</p>"
                "</div>"
            )
    
    def open_document_full(self):
        """Open the current document in full view with the current article selected"""
        if not self.current_document:
            return
            
        try:
            # Prepare the document data to send
            document_data = dict(self.current_document)
            
            # If we have a specific article selected, include its ID
            if self.current_article and 'id' in self.current_article:
                document_data['article_id'] = self.current_article['id']
            elif self.current_article and 'article_number' in self.current_article:
                document_data['article_number'] = self.current_article['article_number']
            
            # Emit the signal with the document data
            self.document_opened.emit(document_data)
            
        except Exception as e:
            self.logger.error(f"Belge açma hatası: {e}")
            # Fallback to basic document data if there's an error
            self.document_opened.emit(self.current_document)
    
    def clear(self):
        """Clear the preview"""
        self.current_document = None
        self.current_article = None
        self.title_label.setText("Belge Önizleme")
        self.content.setHtml(
            "<div style='color: #666; font-style: italic; text-align: center; margin-top: 50px;'>"
            "Bir belge seçin veya arama yapın..."
            "</div>"
        )
        self.open_full_btn.setEnabled(False)
    
    def show_loading(self, message: str = "Yükleniyor..."):
        """Show loading indicator"""
        self.content.setHtml(
            f"<div style='color: #666; font-style: italic; text-align: center; margin-top: 50px;'>{message}</div>"
        )
