"""
Document Viewer Widget - Displays document content with rich text formatting and navigation
"""

import logging
from typing import Optional, Dict, List

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QTextDocument, QTextCursor, QTextCharFormat, QFont, QTextFormat, QColor, QTextBlockFormat, QTextLength
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QScrollArea, QFrame, QSplitter, QToolBar, QAction
)

class DocumentViewer(QWidget):
    """Rich document viewer with navigation and search capabilities"""
    
    # Signals
    document_loaded = pyqtSignal(bool)  # Success status
    search_requested = pyqtSignal(str)  # Search text
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_document = None
        self.search_results = []
        self.current_search_index = -1
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor("yellow"))
        
        self.init_ui()
        self.setup_shortcuts()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self.toolbar = QToolBar("Araç Çubuğu")
        self.toolbar.setIconSize(QSize(16, 16))
        layout.addWidget(self.toolbar)
        
        # Document view
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_edit.setFrameStyle(QFrame.NoFrame)
        
        # Navigation panel (table of contents)
        self.toc_widget = QWidget()
        self.toc_widget.setMaximumWidth(250)
        self.toc_layout = QVBoxLayout(self.toc_widget)
        self.toc_layout.setContentsMargins(5, 5, 5, 5)
        
        toc_label = QLabel("İçindekiler")
        toc_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        self.toc_layout.addWidget(toc_label)
        
        self.toc_scroll = QScrollArea()
        self.toc_scroll.setWidgetResizable(True)
        self.toc_scroll.setWidget(self.toc_widget)
        self.toc_scroll.setFrameStyle(QFrame.NoFrame)
        
        # Splitter for TOC and document
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.toc_scroll)
        self.splitter.addWidget(self.text_edit)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        
        layout.addWidget(self.splitter)
        
        # Status bar
        self.status_bar = QLabel()
        self.status_bar.setStyleSheet("padding: 3px; border-top: 1px solid #ddd;")
        layout.addWidget(self.status_bar)
        
        # Setup toolbar actions
        self.setup_toolbar()
    
    def setup_toolbar(self):
        """Setup toolbar actions"""
        # Navigation actions
        prev_action = QAction("Önceki", self)
        prev_action.setShortcut("Ctrl+Left")
        prev_action.triggered.connect(self.navigate_back)
        
        next_action = QAction("Sonraki", self)
        next_action.setShortcut("Ctrl+Right")
        next_action.triggered.connect(self.navigate_forward)
        
        # Zoom actions
        zoom_in = QAction("Yakınlaştır", self)
        zoom_in.setShortcut("Ctrl++")
        zoom_in.triggered.connect(self.zoom_in)
        
        zoom_out = QAction("Uzaklaştır", self)
        zoom_out.setShortcut("Ctrl+-")
        zoom_out.triggered.connect(self.zoom_out)
        
        # Add actions to toolbar
        self.toolbar.addAction(prev_action)
        self.toolbar.addAction(next_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(zoom_in)
        self.toolbar.addAction(zoom_out)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Search shortcuts
        self.find_action = QAction("Bul", self)
        self.find_action.setShortcut("Ctrl+F")
        self.find_action.triggered.connect(self.show_search_dialog)
        self.addAction(self.find_action)
    
    def load_document(self, document_data: Dict):
        """Load document content into the viewer"""
        try:
            self.current_document = document_data
            
            # Clear previous content
            self.text_edit.clear()
            
            # Set document title
            title = document_data.get('title', 'Başlıksız Belge')
            self.setWindowTitle(title)
            
            # Format and set document content
            cursor = self.text_edit.textCursor()
            
            # Title
            title_format = QTextCharFormat()
            title_format.setFontPointSize(16)
            title_format.setFontWeight(QFont.Bold)
            cursor.setCharFormat(title_format)
            cursor.insertText(title + "\n\n")
            
            # Metadata
            meta_format = QTextCharFormat()
            meta_format.setFontPointSize(10)
            meta_format.setForeground(Qt.gray)
            cursor.setCharFormat(meta_format)
            
            # Add metadata if available
            if 'law_number' in document_data and document_data['law_number']:
                cursor.insertText(f"Kanun No: {document_data['law_number']} | ")
                
            if 'publication_date' in document_data and document_data['publication_date']:
                cursor.insertText(f"Yayım Tarihi: {document_data['publication_date']} | ")
                
            if 'effective_date' in document_data and document_data['effective_date']:
                cursor.insertText(f"Yürürlük Tarihi: {document_data['effective_date']}")
            
            cursor.insertText("\n\n")
            
            # Document content
            content_format = QTextCharFormat()
            content_format.setFontPointSize(11)
            cursor.setCharFormat(content_format)
            
            # Process and insert content
            content = document_data.get('content', '')
            self.process_and_insert_content(cursor, content)
            
            # Move to top
            self.text_edit.moveCursor(QTextCursor.Start)
            
            # Update status
            self.update_status("Belge yüklendi")
            self.document_loaded.emit(True)
            
            # Generate TOC
            self.generate_toc()
            
        except Exception as e:
            self.logger.error(f"Belge yükleme hatası: {e}")
            self.document_loaded.emit(False)
    
    def process_and_insert_content(self, cursor, content: str):
        """Process document content and insert with formatting"""
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        
        for para in paragraphs:
            if not para.strip():
                cursor.insertBlock()
                continue
                
            # Check for headings
            if para.strip().startswith('MADDE') or para.strip().startswith('Madde'):
                # Format as heading
                heading_format = QTextCharFormat()
                heading_format.setFontWeight(QFont.Bold)
                heading_format.setFontPointSize(12)
                cursor.setCharFormat(heading_format)
                cursor.insertText(para.strip())
            else:
                # Regular paragraph
                para_format = QTextCharFormat()
                para_format.setFontPointSize(11)
                cursor.setCharFormat(para_format)
                cursor.insertText(para.strip())
            
            # Add spacing between paragraphs
            cursor.insertBlock()
    
    def generate_toc(self):
        """Generate table of contents from document"""
        # Clear existing TOC
        while self.toc_layout.count() > 1:  # Keep the title label
            item = self.toc_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        # Find all headings in the document
        doc = self.text_edit.document()
        cursor = QTextCursor(doc)
        
        for block in doc:
            if block.text().strip().startswith(('MADDE', 'Madde')):
                btn = QPushButton(block.text())
                btn.setStyleSheet("text-align: left; padding: 2px 5px;")
                btn.setFlat(True)
                btn.clicked.connect(lambda checked, c=cursor: self.scroll_to_heading(c))
                self.toc_layout.addWidget(btn)
    
    def scroll_to_heading(self, cursor):
        """Scroll to the selected heading"""
        self.text_ensureVisible(cursor)
        self.text_edit.setTextCursor(cursor)
    
    def search_in_document(self, text: str):
        """Search for text in the document"""
        if not text:
            return
            
        self.search_text = text
        self.search_results = []
        self.current_search_index = -1
        
        # Clear previous highlights
        self.clear_highlights()
        
        # Find all occurrences
        doc = self.text_edit.document()
        cursor = QTextCursor(doc)
        
        while not cursor.isNull() and not cursor.atEnd():
            cursor = doc.find(text, cursor, QTextDocument.FindWholeWords)
            if not cursor.isNull():
                self.search_results.append(cursor.position())
                cursor.mergeCharFormat(self.highlight_format)
        
        if self.search_results:
            self.current_search_index = 0
            self.navigate_to_search_result()
            self.update_status(f"{len(self.search_results)} eşleşme bulundu")
        else:
            self.update_status("Eşleşme bulunamadı")
    
    def navigate_to_search_result(self):
        """Navigate to the current search result"""
        if not self.search_results or self.current_search_index < 0:
            return
            
        cursor = self.text_edit.textCursor()
        cursor.setPosition(self.search_results[self.current_search_index])
        self.text_edit.setTextCursor(cursor)
        self.text_edit.centerCursor()
        
        self.update_status(f"{self.current_search_index + 1}/{len(self.search_results)}")
    
    def navigate_to_next_result(self):
        """Navigate to next search result"""
        if not self.search_results:
            return
            
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self.navigate_to_search_result()
    
    def navigate_to_previous_result(self):
        """Navigate to previous search result"""
        if not self.search_results:
            return
            
        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        self.navigate_to_search_result()
    
    def clear_highlights(self):
        """Clear search highlights"""
        cursor = self.text_edit.textCursor()
        cursor.select(QTextCursor.Document)
        
        fmt = QTextCharFormat()
        fmt.setBackground(Qt.transparent)
        cursor.mergeCharFormat(fmt)
    
    def zoom_in(self):
        """Zoom in the document"""
        current_size = self.text_edit.font().pointSize()
        if current_size < 36:  # Max zoom level
            self.text_edit.setFontPointSize(current_size + 1)
    
    def zoom_out(self):
        """Zoom out the document"""
        current_size = self.text_edit.font().pointSize()
        if current_size > 8:  # Min zoom level
            self.text_edit.setFontPointSize(current_size - 1)
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_bar.setText(message)
    
    def show_search_dialog(self):
        """Show search dialog"""
        from PyQt5.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(self, 'Ara', 'Aranacak metin:')
        if ok and text:
            self.search_in_document(text)
    
    def navigate_back(self):
        """Navigate back in history"""
        # TODO: Implement navigation history
        pass
    
    def navigate_forward(self):
        """Navigate forward in history"""
        # TODO: Implement navigation history
        pass
