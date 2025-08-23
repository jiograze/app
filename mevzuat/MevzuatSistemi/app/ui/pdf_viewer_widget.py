"""
PDF Belge Görüntüleyici Widget'ı
PyMuPDF (fitz) kullanarak PDF dosyalarını görüntüler
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSpinBox, QSlider, QFrame, QScrollArea,
    QSizePolicy, QSplitter, QTextEdit, QGroupBox,
    QToolBar, QAction, QFileDialog, QMessageBox
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QSize, QTimer, QThread, pyqtSignal
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QFont, QIcon, QPixmap, QImage,
    QPalette, QColor, QBrush
)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None

class PDFRenderThread(QThread):
    """PDF sayfa render thread'i"""
    
    page_rendered = pyqtSignal(int, QPixmap)  # page_number, pixmap
    render_error = pyqtSignal(str)
    
    def __init__(self, pdf_document, page_number, zoom_factor=1.0):
        super().__init__()
        self.pdf_document = pdf_document
        self.page_number = page_number
        self.zoom_factor = zoom_factor
        
    def run(self):
        """Thread'i çalıştır"""
        try:
            if not self.pdf_document:
                self.render_error.emit("PDF dökümanı yüklenmedi")
                return
                
            # Sayfayı al
            page = self.pdf_document[self.page_number]
            
            # Zoom matrisi oluştur
            mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            
            # Sayfayı render et
            pix = page.get_pixmap(matrix=mat)
            
            # QPixmap'e dönüştür
            img_data = pix.tobytes("ppm")
            qimage = QImage()
            qimage.loadFromData(img_data)
            
            pixmap = QPixmap.fromImage(qimage)
            self.page_rendered.emit(self.page_number, pixmap)
            
        except Exception as e:
            self.render_error.emit(f"Render hatası: {str(e)}")

class PDFViewerWidget(QWidget):
    """PDF belge görüntüleyici ana widget'ı"""
    
    document_loaded = pyqtSignal(str)  # file_path
    page_changed = pyqtSignal(int)     # page_number
    zoom_changed = pyqtSignal(float)   # zoom_factor
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # PDF döküman
        self.pdf_document: Optional[fitz.Document] = None
        self.current_file_path: Optional[str] = None
        
        # Sayfa bilgileri
        self.current_page = 0
        self.total_pages = 0
        self.zoom_factor = 1.0
        
        # Render thread'leri
        self.render_threads: Dict[int, PDFRenderThread] = {}
        
        # UI bileşenleri
        self.page_label: Optional[QLabel] = None
        self.zoom_slider: Optional[QSlider] = None
        self.page_spinbox: Optional[QSpinBox] = None
        self.scroll_area: Optional[QScrollArea] = None
        self.page_display: Optional[QLabel] = None
        
        # Ayarlar
        self.auto_render = True
        self.cache_size = 10  # Sayfa cache boyutu
        
        self.init_ui()
        
    def init_ui(self):
        """UI'yi oluştur"""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Ana görüntüleme alanı
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Sol panel - Sayfa bilgileri
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Orta panel - PDF görüntüleme
        center_panel = self.create_center_panel()
        main_splitter.addWidget(center_panel)
        
        # Sağ panel - Belge bilgileri
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Splitter oranları
        main_splitter.setSizes([200, 600, 200])
        
        layout.addWidget(main_splitter)
        
        # Status bar
        status_bar = self.create_status_bar()
        layout.addWidget(status_bar)
        
        self.setLayout(layout)
        
        # Minimum boyut
        self.setMinimumSize(800, 600)
        
    def create_toolbar(self) -> QToolBar:
        """Toolbar oluştur"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # Dosya aç
        open_action = QAction("📁 Aç", self)
        open_action.triggered.connect(self.open_pdf_file)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # Sayfa navigasyon
        first_page_action = QAction("⏮️ İlk", self)
        first_page_action.triggered.connect(self.go_to_first_page)
        toolbar.addAction(first_page_action)
        
        prev_page_action = QAction("◀️ Önceki", self)
        prev_page_action.triggered.connect(self.go_to_previous_page)
        toolbar.addAction(prev_page_action)
        
        next_page_action = QAction("▶️ Sonraki", self)
        next_page_action.triggered.connect(self.go_to_next_page)
        toolbar.addAction(next_page_action)
        
        last_page_action = QAction("⏭️ Son", self)
        last_page_action.triggered.connect(self.go_to_last_page)
        toolbar.addAction(last_page_action)
        
        toolbar.addSeparator()
        
        # Zoom kontrolleri
        zoom_out_action = QAction("🔍-", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        zoom_in_action = QAction("🔍+", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        return toolbar
        
    def create_left_panel(self) -> QWidget:
        """Sol panel - Sayfa bilgileri"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Sayfa navigasyon grubu
        nav_group = QGroupBox("Sayfa Navigasyonu")
        nav_layout = QVBoxLayout()
        
        # Sayfa numarası
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Sayfa:"))
        
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)
        self.page_spinbox.valueChanged.connect(self.on_page_spinbox_changed)
        page_layout.addWidget(self.page_spinbox)
        
        nav_layout.addLayout(page_layout)
        
        # Toplam sayfa
        self.page_label = QLabel("Toplam: 0 sayfa")
        nav_layout.addWidget(self.page_label)
        
        # Zoom kontrolü
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(25)  # %25
        self.zoom_slider.setMaximum(400)  # %400
        self.zoom_slider.setValue(100)  # %100
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        zoom_layout.addWidget(self.zoom_slider)
        
        nav_layout.addLayout(zoom_layout)
        
        nav_group.setLayout(nav_layout)
        layout.addWidget(nav_group)
        
        # Sayfa önizlemeleri
        preview_group = QGroupBox("Sayfa Önizlemeleri")
        preview_layout = QVBoxLayout()
        
        # TODO: Sayfa thumbnail'ları eklenecek
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def create_center_panel(self) -> QWidget:
        """Orta panel - PDF görüntüleme"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Sayfa görüntüleme label'ı
        self.page_display = QLabel()
        self.page_display.setAlignment(Qt.AlignCenter)
        self.page_display.setMinimumSize(400, 500)
        self.page_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.page_display.setText("PDF dosyası yüklenmedi")
        self.page_display.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px dashed #cccccc;
                color: #666666;
                font-size: 14px;
            }
        """)
        
        self.scroll_area.setWidget(self.page_display)
        layout.addWidget(self.scroll_area)
        
        panel.setLayout(layout)
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Sağ panel - Belge bilgileri"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Belge bilgileri grubu
        info_group = QGroupBox("Belge Bilgileri")
        info_layout = QVBoxLayout()
        
        self.document_info_label = QLabel("Belge yüklenmedi")
        self.document_info_label.setWordWrap(True)
        info_layout.addWidget(self.document_info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # İçindekiler grubu
        toc_group = QGroupBox("İçindekiler")
        toc_layout = QVBoxLayout()
        
        self.toc_text = QTextEdit()
        self.toc_text.setReadOnly(True)
        self.toc_text.setMaximumHeight(200)
        toc_layout.addWidget(self.toc_text)
        
        toc_group.setLayout(toc_layout)
        layout.addWidget(toc_group)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def create_status_bar(self) -> QWidget:
        """Status bar oluştur"""
        status_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Dosya yolu
        self.file_path_label = QLabel("Dosya: Seçilmedi")
        self.file_path_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.file_path_label)
        
        layout.addStretch()
        
        # Sayfa bilgisi
        self.status_page_label = QLabel("Sayfa: 0/0")
        self.status_page_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_page_label)
        
        # Zoom bilgisi
        self.status_zoom_label = QLabel("Zoom: %100")
        self.status_zoom_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_zoom_label)
        
        status_widget.setLayout(layout)
        return status_widget
        
    def open_pdf_file(self):
        """PDF dosyası aç"""
        if not PYMUPDF_AVAILABLE:
            QMessageBox.warning(self, "Hata", "PyMuPDF kütüphanesi yüklenemedi!")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "PDF Dosyası Aç",
            "",
            "PDF Dosyaları (*.pdf);;Tüm Dosyalar (*)"
        )
        
        if file_path:
            self.load_pdf(file_path)
            
    def load_pdf(self, file_path: str):
        """PDF dosyasını yükle"""
        try:
            self.logger.info(f"PDF yükleniyor: {file_path}")
            
            # Mevcut dökümanı kapat
            if self.pdf_document:
                self.pdf_document.close()
                
            # Yeni dökümanı aç
            self.pdf_document = fitz.open(file_path)
            self.current_file_path = file_path
            
            # Sayfa bilgilerini güncelle
            self.total_pages = len(self.pdf_document)
            self.current_page = 0
            
            # UI'yi güncelle
            self.update_ui_after_load()
            
            # İlk sayfayı göster
            self.show_page(0)
            
            # Belge bilgilerini güncelle
            self.update_document_info()
            
            # İçindekileri güncelle
            self.update_table_of_contents()
            
            # Signal gönder
            self.document_loaded.emit(file_path)
            
            self.logger.info(f"PDF başarıyla yüklendi: {self.total_pages} sayfa")
            
        except Exception as e:
            self.logger.error(f"PDF yükleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"PDF yüklenemedi:\n{str(e)}")
            
    def update_ui_after_load(self):
        """PDF yüklendikten sonra UI'yi güncelle"""
        # Sayfa spinbox
        self.page_spinbox.setMaximum(self.total_pages)
        self.page_spinbox.setValue(1)
        
        # Sayfa label
        self.page_label.setText(f"Toplam: {self.total_pages} sayfa")
        
        # Status bar
        self.file_path_label.setText(f"Dosya: {Path(self.current_file_path).name}")
        self.status_page_label.setText(f"Sayfa: 0/{self.total_pages}")
        
        # Sayfa display
        self.page_display.setText(f"PDF yüklendi: {self.total_pages} sayfa")
        
    def show_page(self, page_number: int):
        """Belirli sayfayı göster"""
        if not self.pdf_document or page_number < 0 or page_number >= self.total_pages:
            return
            
        self.current_page = page_number
        
        # UI'yi güncelle
        self.page_spinbox.setValue(page_number + 1)
        self.status_page_label.setText(f"Sayfa: {page_number + 1}/{self.total_pages}")
        
        # Sayfayı render et
        self.render_page(page_number)
        
        # Signal gönder
        self.page_changed.emit(page_number)
        
    def render_page(self, page_number: int):
        """Sayfayı render et"""
        if not self.pdf_document:
            return
            
        # Mevcut render thread'ini durdur
        if page_number in self.render_threads:
            old_thread = self.render_threads[page_number]
            if old_thread.isRunning():
                old_thread.terminate()
                old_thread.wait()
                
        # Yeni render thread'i oluştur
        render_thread = PDFRenderThread(
            self.pdf_document, 
            page_number, 
            self.zoom_factor
        )
        
        # Signal'leri bağla
        render_thread.page_rendered.connect(self.on_page_rendered)
        render_thread.render_error.connect(self.on_render_error)
        
        # Thread'i başlat
        render_thread.start()
        
        # Cache'e ekle
        self.render_threads[page_number] = render_thread
        
        # Cache boyutunu kontrol et
        if len(self.render_threads) > self.cache_size:
            # En eski thread'i kaldır
            oldest_page = min(self.render_threads.keys())
            old_thread = self.render_threads.pop(oldest_page)
            if old_thread.isRunning():
                old_thread.terminate()
                old_thread.wait()
                
    def on_page_rendered(self, page_number: int, pixmap: QPixmap):
        """Sayfa render edildiğinde"""
        if page_number == self.current_page:
            self.page_display.setPixmap(pixmap)
            self.page_display.setMinimumSize(pixmap.size())
            
    def on_render_error(self, error_message: str):
        """Render hatası olduğunda"""
        self.logger.error(f"Render hatası: {error_message}")
        self.page_display.setText(f"Render hatası: {error_message}")
        
    def go_to_first_page(self):
        """İlk sayfaya git"""
        self.show_page(0)
        
    def go_to_previous_page(self):
        """Önceki sayfaya git"""
        if self.current_page > 0:
            self.show_page(self.current_page - 1)
            
    def go_to_next_page(self):
        """Sonraki sayfaya git"""
        if self.current_page < self.total_pages - 1:
            self.show_page(self.current_page + 1)
            
    def go_to_last_page(self):
        """Son sayfaya git"""
        self.show_page(self.total_pages - 1)
        
    def on_page_spinbox_changed(self, value: int):
        """Sayfa spinbox değiştiğinde"""
        page_number = value - 1
        if page_number != self.current_page:
            self.show_page(page_number)
            
    def zoom_in(self):
        """Yakınlaştır"""
        new_zoom = min(self.zoom_factor * 1.25, 4.0)
        self.set_zoom(new_zoom)
        
    def zoom_out(self):
        """Uzaklaştır"""
        new_zoom = max(self.zoom_factor / 1.25, 0.25)
        self.set_zoom(new_zoom)
        
    def set_zoom(self, zoom_factor: float):
        """Zoom faktörünü ayarla"""
        self.zoom_factor = zoom_factor
        
        # Slider'ı güncelle
        self.zoom_slider.setValue(int(zoom_factor * 100))
        
        # Status bar'ı güncelle
        self.status_zoom_label.setText(f"Zoom: %{int(zoom_factor * 100)}")
        
        # Mevcut sayfayı yeniden render et
        if self.pdf_document:
            self.render_page(self.current_page)
            
        # Signal gönder
        self.zoom_changed.emit(zoom_factor)
        
    def on_zoom_slider_changed(self, value: int):
        """Zoom slider değiştiğinde"""
        zoom_factor = value / 100.0
        if abs(zoom_factor - self.zoom_factor) > 0.01:
            self.set_zoom(zoom_factor)
            
    def update_document_info(self):
        """Belge bilgilerini güncelle"""
        if not self.pdf_document:
            self.document_info_label.setText("Belge yüklenmedi")
            return
            
        try:
            metadata = self.pdf_document.metadata
            
            info_text = f"""
            <b>Dosya Adı:</b> {Path(self.current_file_path).name}<br>
            <b>Toplam Sayfa:</b> {self.total_pages}<br>
            <b>Dosya Boyutu:</b> {Path(self.current_file_path).stat().st_size / 1024:.1f} KB<br>
            """
            
            if metadata.get('title'):
                info_text += f"<b>Başlık:</b> {metadata['title']}<br>"
            if metadata.get('author'):
                info_text += f"<b>Yazar:</b> {metadata['author']}<br>"
            if metadata.get('subject'):
                info_text += f"<b>Konu:</b> {metadata['subject']}<br>"
            if metadata.get('creator'):
                info_text += f"<b>Oluşturan:</b> {metadata['creator']}<br>"
            if metadata.get('producer'):
                info_text += f"<b>Üretici:</b> {metadata['producer']}<br>"
                
            self.document_info_label.setText(info_text)
            
        except Exception as e:
            self.logger.error(f"Metadata güncelleme hatası: {e}")
            self.document_info_label.setText("Belge bilgileri alınamadı")
            
    def update_table_of_contents(self):
        """İçindekiler tablosunu güncelle"""
        if not self.pdf_document:
            self.toc_text.setText("İçindekiler yok")
            return
            
        try:
            toc = self.pdf_document.get_toc()
            
            if not toc:
                self.toc_text.setText("İçindekiler bulunamadı")
                return
                
            toc_text = ""
            for level, title, page in toc:
                indent = "  " * (level - 1)
                toc_text += f"{indent}• {title} (Sayfa {page + 1})\n"
                
            self.toc_text.setText(toc_text)
            
        except Exception as e:
            self.logger.error(f"İçindekiler güncelleme hatası: {e}")
            self.toc_text.setText("İçindekiler alınamadı")
            
    def closeEvent(self, event):
        """Widget kapatılırken"""
        # Render thread'lerini temizle
        for thread in self.render_threads.values():
            if thread.isRunning():
                thread.terminate()
                thread.wait()
                
        # PDF dökümanını kapat
        if self.pdf_document:
            self.pdf_document.close()
            
        event.accept()
        
    def get_current_page_content(self) -> str:
        """Mevcut sayfanın metin içeriğini al"""
        if not self.pdf_document or self.current_page >= self.total_pages:
            return ""
            
        try:
            page = self.pdf_document[self.current_page]
            text = page.get_text()
            return text
        except Exception as e:
            self.logger.error(f"Metin çıkarma hatası: {e}")
            return ""
            
    def search_in_current_page(self, search_term: str) -> list:
        """Mevcut sayfada arama yap"""
        if not self.pdf_document or self.current_page >= self.total_pages:
            return []
            
        try:
            page = self.pdf_document[self.current_page]
            text_instances = page.search_for(search_term)
            return text_instances
        except Exception as e:
            self.logger.error(f"Sayfa arama hatası: {e}")
            return []
