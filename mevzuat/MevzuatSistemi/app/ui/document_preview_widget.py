"""
Belge Önizleme Widget'ı
Belge içeriğini metin olarak gösterir ve arama sonuçlarını highlight eder
"""

import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLabel, QPushButton, QFrame, QGroupBox, QSplitter,
    QListWidget, QListWidgetItem, QHeaderView, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QMenu, QAction,
    QLineEdit, QComboBox, QCheckBox, QProgressBar
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QTimer, QThread, pyqtSignal
)
from PyQt5.QtGui import (
    QFont, QTextCursor, QTextCharFormat, QColor, 
    QBrush, QIcon, QPixmap, QPainter
)

class DocumentPreviewWidget(QWidget):
    """Belge önizleme ana widget'ı"""
    
    document_selected = pyqtSignal(dict)  # document_data
    text_selected = pyqtSignal(str)       # selected_text
    search_requested = pyqtSignal(str)    # search_term
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Mevcut belge
        self.current_document: Optional[Dict[str, Any]] = None
        self.current_content: str = ""
        
        # Arama ayarları
        self.search_term: str = ""
        self.search_results: List[Dict[str, Any]] = []
        self.current_highlight_index: int = -1
        
        # UI bileşenleri
        self.content_text: Optional[QTextEdit] = None
        self.search_input: Optional[QLineEdit] = None
        self.search_results_list: Optional[QListWidget] = None
        self.document_info_label: Optional[QLabel] = None
        self.metadata_table: Optional[QTableWidget] = None
        
        # Highlight formatları
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QBrush(QColor(255, 255, 0, 100)))  # Sarı, yarı şeffaf
        
        self.current_highlight_format = QTextCharFormat()
        self.current_highlight_format.setBackground(QBrush(QColor(255, 165, 0, 150)))  # Turuncu
        
        self.init_ui()
        
    def init_ui(self):
        """UI'yi oluştur"""
        layout = QVBoxLayout()
        
        # Üst panel - Arama ve kontroller
        top_panel = self.create_top_panel()
        layout.addWidget(top_panel)
        
        # Ana görüntüleme alanı
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Sol panel - Belge içeriği
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Sağ panel - Belge bilgileri ve arama sonuçları
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Splitter oranları
        main_splitter.setSizes([600, 300])
        
        layout.addWidget(main_splitter)
        
        # Alt panel - Durum bilgileri
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)
        
        self.setLayout(layout)
        
        # Minimum boyut
        self.setMinimumSize(700, 500)
        
    def create_top_panel(self) -> QWidget:
        """Üst panel - Arama ve kontroller"""
        panel = QWidget()
        layout = QHBoxLayout()
        
        # Arama grubu
        search_group = QGroupBox("Metin Arama")
        search_layout = QHBoxLayout()
        
        # Arama input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Aranacak metni girin...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        
        # Arama butonu
        search_button = QPushButton("🔍 Ara")
        search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(search_button)
        
        # Temizle butonu
        clear_button = QPushButton("❌ Temizle")
        clear_button.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_button)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Navigasyon grubu
        nav_group = QGroupBox("Navigasyon")
        nav_layout = QHBoxLayout()
        
        # Önceki sonuç
        prev_result_button = QPushButton("◀️ Önceki")
        prev_result_button.clicked.connect(self.go_to_previous_result)
        nav_layout.addWidget(prev_result_button)
        
        # Sonraki sonuç
        next_result_button = QPushButton("▶️ Sonraki")
        next_result_button.clicked.connect(self.go_to_next_result)
        nav_layout.addWidget(next_result_button)
        
        # Sonuç sayısı
        self.result_count_label = QLabel("0 sonuç")
        self.result_count_label.setStyleSheet("color: #666; font-size: 11px;")
        nav_layout.addWidget(self.result_count_label)
        
        nav_group.setLayout(nav_layout)
        layout.addWidget(nav_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def create_left_panel(self) -> QWidget:
        """Sol panel - Belge içeriği"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # İçerik grubu
        content_group = QGroupBox("Belge İçeriği")
        content_layout = QVBoxLayout()
        
        # İçerik metin editörü
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setFont(QFont("Consolas", 10))
        self.content_text.setLineWrapMode(QTextEdit.NoWrap)
        self.content_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
                line-height: 1.4;
            }
        """)
        
        # Metin seçimi sinyali
        self.content_text.selectionChanged.connect(self.on_text_selection_changed)
        
        content_layout.addWidget(self.content_text)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        panel.setLayout(layout)
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Sağ panel - Belge bilgileri ve arama sonuçları"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Belge bilgileri grubu
        info_group = QGroupBox("Belge Bilgileri")
        info_layout = QVBoxLayout()
        
        self.document_info_label = QLabel("Belge yüklenmedi")
        self.document_info_label.setWordWrap(True)
        self.document_info_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        info_layout.addWidget(self.document_info_label)
        
        # Metadata tablosu
        self.metadata_table = QTableWidget()
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setHorizontalHeaderLabels(["Özellik", "Değer"])
        self.metadata_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.metadata_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.metadata_table.setMaximumHeight(150)
        self.metadata_table.setAlternatingRowColors(True)
        info_layout.addWidget(self.metadata_table)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Arama sonuçları grubu
        results_group = QGroupBox("Arama Sonuçları")
        results_layout = QVBoxLayout()
        
        self.search_results_list = QListWidget()
        self.search_results_list.setMaximumHeight(200)
        self.search_results_list.itemClicked.connect(self.on_search_result_clicked)
        self.search_results_list.setAlternatingRowColors(True)
        results_layout.addWidget(self.search_results_list)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def create_bottom_panel(self) -> QWidget:
        """Alt panel - Durum bilgileri"""
        panel = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Belge durumu
        self.document_status_label = QLabel("Belge yüklenmedi")
        self.document_status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.document_status_label)
        
        layout.addStretch()
        
        # İçerik bilgileri
        self.content_info_label = QLabel("0 karakter, 0 satır")
        self.content_info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.content_info_label)
        
        # Arama durumu
        self.search_status_label = QLabel("")
        self.search_status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.search_status_label)
        
        panel.setLayout(layout)
        return panel
        
    def load_document(self, document_data: Dict[str, Any]):
        """Belge yükle"""
        try:
            self.logger.info(f"Belge yükleniyor: {document_data.get('title', 'Bilinmeyen')}")
            
            self.current_document = document_data
            
            # İçeriği yükle
            content = document_data.get('content', '')
            self.current_content = content
            
            # UI'yi güncelle
            self.update_content_display()
            self.update_document_info()
            self.update_metadata_table()
            self.update_status_labels()
            
            # Arama sonuçlarını temizle
            self.clear_search()
            
            # Signal gönder
            self.document_selected.emit(document_data)
            
            self.logger.info("Belge başarıyla yüklendi")
            
        except Exception as e:
            self.logger.error(f"Belge yükleme hatası: {e}")
            self.show_error_message(f"Belge yüklenemedi: {str(e)}")
            
    def update_content_display(self):
        """İçerik görüntülemeyi güncelle"""
        if not self.content_text:
            return
            
        # Mevcut highlight'ları temizle
        self.clear_highlights()
        
        # İçeriği ayarla
        self.content_text.setPlainText(self.current_content)
        
        # Cursor'ı başa al
        cursor = self.content_text.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.content_text.setTextCursor(cursor)
        
    def update_document_info(self):
        """Belge bilgilerini güncelle"""
        if not self.document_info_label or not self.current_document:
            return
            
        doc = self.current_document
        
        info_text = f"""
        <b>Başlık:</b> {doc.get('title', 'Bilinmeyen')}<br>
        <b>Tür:</b> {doc.get('document_type', 'Bilinmeyen')}<br>
        <b>Kanun No:</b> {doc.get('law_number', 'Belirtilmemiş')}<br>
        <b>Oluşturulma:</b> {doc.get('created_at', 'Bilinmeyen')}<br>
        <b>Dosya Yolu:</b> {doc.get('file_path', 'Bilinmeyen')}<br>
        <b>Madde Sayısı:</b> {doc.get('article_count', 0)}
        """
        
        self.document_info_label.setText(info_text)
        
    def update_metadata_table(self):
        """Metadata tablosunu güncelle"""
        if not self.metadata_table or not self.current_document:
            return
            
        doc = self.current_document
        metadata = doc.get('metadata', {})
        
        # Tabloyu temizle
        self.metadata_table.setRowCount(0)
        
        if not metadata:
            return
            
        # Metadata satırlarını ekle
        for key, value in metadata.items():
            row = self.metadata_table.rowCount()
            self.metadata_table.insertRow(row)
            
            key_item = QTableWidgetItem(str(key))
            key_item.setBackground(QBrush(QColor(240, 240, 240)))
            self.metadata_table.setItem(row, 0, key_item)
            
            value_item = QTableWidgetItem(str(value))
            self.metadata_table.setItem(row, 1, value_item)
            
    def update_status_labels(self):
        """Durum label'larını güncelle"""
        if not self.current_document:
            self.document_status_label.setText("Belge yüklenmedi")
            self.content_info_label.setText("0 karakter, 0 satır")
            return
            
        # Belge durumu
        doc = self.current_document
        status_text = f"Yüklendi: {doc.get('title', 'Bilinmeyen')}"
        self.document_status_label.setText(status_text)
        
        # İçerik bilgileri
        content = self.current_content
        char_count = len(content)
        line_count = content.count('\n') + 1
        content_text = f"{char_count:,} karakter, {line_count} satır"
        self.content_info_label.setText(content_text)
        
    def perform_search(self):
        """Arama yap"""
        search_term = self.search_input.text().strip()
        if not search_term:
            return
            
        self.search_term = search_term
        self.search_in_content(search_term)
        
    def search_in_content(self, search_term: str):
        """İçerikte arama yap"""
        if not self.current_content:
            return
            
        try:
            # Case-insensitive arama
            pattern = re.compile(re.escape(search_term), re.IGNORECASE)
            matches = list(pattern.finditer(self.current_content))
            
            self.search_results = []
            for match in matches:
                self.search_results.append({
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group(),
                    'line': self.get_line_number(match.start())
                })
            
            # Sonuçları göster
            self.display_search_results()
            
            # İlk sonucu highlight et
            if self.search_results:
                self.current_highlight_index = 0
                self.highlight_current_result()
            else:
                self.current_highlight_index = -1
                
            # Durum güncelle
            self.update_search_status()
            
        except Exception as e:
            self.logger.error(f"Arama hatası: {e}")
            self.show_error_message(f"Arama yapılamadı: {str(e)}")
            
    def get_line_number(self, position: int) -> int:
        """Pozisyona göre satır numarasını al"""
        if not self.current_content:
            return 1
            
        return self.current_content[:position].count('\n') + 1
        
    def display_search_results(self):
        """Arama sonuçlarını göster"""
        if not self.search_results_list:
            return
            
        # Listeyi temizle
        self.search_results_list.clear()
        
        if not self.search_results:
            return
            
        # Sonuçları ekle
        for i, result in enumerate(self.search_results):
            item = QListWidgetItem()
            
            # HTML formatında metin
            display_text = f"""
            <div style="padding: 4px;">
                <b>Sonuç {i+1}</b> - Satır {result['line']}<br>
                <span style="color: #666; font-size: 11px;">
                    {result['text'][:50]}{'...' if len(result['text']) > 50 else ''}
                </span>
            </div>
            """
            
            item.setText(display_text)
            item.setData(Qt.UserRole, result)
            
            self.search_results_list.addItem(item)
            
        # Sonuç sayısını güncelle
        self.result_count_label.setText(f"{len(self.search_results)} sonuç")
        
    def highlight_current_result(self):
        """Mevcut sonucu highlight et"""
        if not self.search_results or self.current_highlight_index < 0:
            return
            
        # Önceki highlight'ları temizle
        self.clear_highlights()
        
        # Tüm sonuçları highlight et
        self.highlight_all_results()
        
        # Mevcut sonucu özel highlight et
        current_result = self.search_results[self.current_highlight_index]
        self.highlight_text_range(
            current_result['start'], 
            current_result['end'], 
            self.current_highlight_format
        )
        
        # Cursor'ı mevcut sonuca taşı
        self.scroll_to_position(current_result['start'])
        
    def highlight_all_results(self):
        """Tüm arama sonuçlarını highlight et"""
        if not self.content_text or not self.search_results:
            return
            
        for result in self.search_results:
            self.highlight_text_range(
                result['start'], 
                result['end'], 
                self.highlight_format
            )
            
    def highlight_text_range(self, start: int, end: int, format: QTextCharFormat):
        """Belirli metin aralığını highlight et"""
        if not self.content_text:
            return
            
        cursor = self.content_text.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.mergeCharFormat(format)
        
    def clear_highlights(self):
        """Tüm highlight'ları temizle"""
        if not self.content_text:
            return
            
        # Format'ı sıfırla
        cursor = self.content_text.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setCharFormat(QTextCharFormat())
        
        # İçeriği yeniden yükle
        self.content_text.setPlainText(self.current_content)
        
    def scroll_to_position(self, position: int):
        """Belirli pozisyona scroll yap"""
        if not self.content_text:
            return
            
        cursor = self.content_text.textCursor()
        cursor.setPosition(position)
        self.content_text.setTextCursor(cursor)
        
        # Pozisyonu görünür yap
        self.content_text.ensureCursorVisible()
        
    def go_to_previous_result(self):
        """Önceki sonuca git"""
        if not self.search_results:
            return
            
        if self.current_highlight_index > 0:
            self.current_highlight_index -= 1
        else:
            self.current_highlight_index = len(self.search_results) - 1
            
        self.highlight_current_result()
        
    def go_to_next_result(self):
        """Sonraki sonuca git"""
        if not self.search_results:
            return
            
        if self.current_highlight_index < len(self.search_results) - 1:
            self.current_highlight_index += 1
        else:
            self.current_highlight_index = 0
            
        self.highlight_current_result()
        
    def on_search_result_clicked(self, item: QListWidgetItem):
        """Arama sonucu tıklandığında"""
        result_data = item.data(Qt.UserRole)
        if not result_data:
            return
            
        # Sonucu bul ve highlight et
        for i, result in enumerate(self.search_results):
            if (result['start'] == result_data['start'] and 
                result['end'] == result_data['end']):
                self.current_highlight_index = i
                self.highlight_current_result()
                break
                
    def on_text_selection_changed(self):
        """Metin seçimi değiştiğinde"""
        cursor = self.content_text.textCursor()
        selected_text = cursor.selectedText()
        
        if selected_text:
            self.text_selected.emit(selected_text)
            
    def clear_search(self):
        """Aramayı temizle"""
        self.search_term = ""
        self.search_results = []
        self.current_highlight_index = -1
        
        # Input'u temizle
        if self.search_input:
            self.search_input.clear()
            
        # Sonuçları temizle
        if self.search_results_list:
            self.search_results_list.clear()
            
        # Highlight'ları temizle
        self.clear_highlights()
        
        # Label'ları güncelle
        self.result_count_label.setText("0 sonuç")
        self.search_status_label.setText("")
        
    def update_search_status(self):
        """Arama durumunu güncelle"""
        if not self.search_results:
            self.search_status_label.setText("Sonuç bulunamadı")
        else:
            current = self.current_highlight_index + 1
            total = len(self.search_results)
            self.search_status_label.setText(f"Sonuç {current}/{total}")
            
    def show_error_message(self, message: str):
        """Hata mesajı göster"""
        self.logger.error(message)
        # TODO: Status bar'da hata mesajı göster
        
    def get_selected_text(self) -> str:
        """Seçili metni al"""
        if not self.content_text:
            return ""
            
        cursor = self.content_text.textCursor()
        return cursor.selectedText()
        
    def copy_selected_text(self):
        """Seçili metni kopyala"""
        selected_text = self.get_selected_text()
        if selected_text:
            clipboard = self.parent().window().clipboard()
            clipboard.setText(selected_text)
            
    def export_content(self, file_path: str):
        """İçeriği dosyaya export et"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.current_content)
            self.logger.info(f"İçerik export edildi: {file_path}")
        except Exception as e:
            self.logger.error(f"Export hatası: {e}")
            self.show_error_message(f"Export yapılamadı: {str(e)}")
            
    def get_document_summary(self) -> Dict[str, Any]:
        """Belge özeti al"""
        if not self.current_document:
            return {}
            
        doc = self.current_document
        content = self.current_content
        
        summary = {
            'title': doc.get('title', ''),
            'type': doc.get('document_type', ''),
            'law_number': doc.get('law_number', ''),
            'total_chars': len(content),
            'total_lines': content.count('\n') + 1,
            'word_count': len(content.split()),
            'created_at': doc.get('created_at', ''),
            'file_path': doc.get('file_path', '')
        }
        
        return summary
