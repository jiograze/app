"""
Ana pencere - PyQt5 tabanlı kullanıcı arayüzü
"""

import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QTextEdit, QLabel, QComboBox, QCheckBox,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QAction, QFileDialog,
    QMessageBox, QTabWidget, QGroupBox, QSpinBox, QSlider,
    QApplication, QHeaderView, QFrame
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPoint, QUrl
)
from PyQt5.QtGui import (
    QIcon, QFont, QPixmap, QPalette, QColor, QDragEnterEvent, QDropEvent
)

from .search_widget import SearchWidget
from .result_widget import ResultWidget
from .document_tree_widget import DocumentTreeContainer
from .stats_widget import StatsWidget
from .settings_dialog import SettingsDialog
from ..core.search_engine import SearchResult

class FileWatcherStatus(QWidget):
    """Dosya izleyici durum widget'ı"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status LED
        self.status_led = QLabel("●")
        self.status_led.setStyleSheet("color: red; font-size: 14px;")
        
        # Status text
        self.status_text = QLabel("File Watcher: Stopped")
        
        # Queue info
        self.queue_info = QLabel("Queue: 0")
        
        layout.addWidget(self.status_led)
        layout.addWidget(self.status_text)
        layout.addWidget(self.queue_info)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_status(self, is_running: bool, queue_size: int = 0):
        """Durumu güncelle"""
        if is_running:
            self.status_led.setStyleSheet("color: green; font-size: 14px;")
            self.status_text.setText("File Watcher: Running")
        else:
            self.status_led.setStyleSheet("color: red; font-size: 14px;")
            self.status_text.setText("File Watcher: Stopped")
        
        self.queue_info.setText(f"Queue: {queue_size}")

class MainWindow(QMainWindow):
    """Ana uygulama penceresi"""
    
    def __init__(self, config, db, search_engine, document_processor, file_watcher):
        super().__init__()
        
        self.config = config
        self.db = db
        self.search_engine = search_engine
        self.document_processor = document_processor
        self.file_watcher = file_watcher
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # UI state
        self.last_search_results: List[SearchResult] = []
        self.current_document = None
        
        # Timers
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_status)
        self.status_update_timer.start(5000)  # 5 saniye
        
        # Drag & Drop desteği
        self.setAcceptDrops(True)
        
        self.init_ui()
        self.load_settings()
        
        # Favoriler listesini yükle
        self.refresh_favorites()
        
        self.logger.info("Ana pencere başlatıldı")
    
    def init_ui(self):
        """UI bileşenlerini oluştur"""
        self.setWindowTitle("Mevzuat Belge Analiz & Sorgulama Sistemi v1.0.2")
        self.setGeometry(100, 100, 1400, 800)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QVBoxLayout(central_widget)
        
        # Menu bar
        self.create_menu_bar()
        
        # Toolbar
        self.create_toolbar()
        
        # Ana içerik alanı
        content_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # Sol panel
        left_panel = self.create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Orta panel (arama ve sonuçlar)
        middle_panel = self.create_middle_panel()
        content_splitter.addWidget(middle_panel)
        
        # Sağ panel (detaylar)
        right_panel = self.create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Splitter oranları
        content_splitter.setSizes([300, 700, 400])
        
        # Status bar
        self.create_status_bar()
        
        # Stil uygula
        self.apply_theme()
    
    def create_menu_bar(self):
        """Menu çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu('📁 Dosya')
        
        # Belge ekleme seçenekleri
        add_files_action = QAction('➕ Dosya Seçerek Belge Ekle', self)
        add_files_action.setShortcut('Ctrl+O')
        add_files_action.setStatusTip('Bilgisayarınızdan dosya seçerek mevzuat belgesi ekleyin')
        add_files_action.triggered.connect(self.select_and_process_files)
        file_menu.addAction(add_files_action)
        
        # Raw klasör tarama
        scan_action = QAction('🔍 Raw Klasörü Tara', self)
        scan_action.setStatusTip('Raw klasöründeki işlenmemiş dosyaları sistem otomatik tarar')
        scan_action.triggered.connect(self.scan_raw_folder)
        file_menu.addAction(scan_action)
        
        file_menu.addSeparator()
        
        # Dışa aktar
        export_action = QAction('📄 PDF Rapor Oluştur', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction('🚪 Çıkış', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Araçlar menüsü
        tools_menu = menubar.addMenu('🔧 Araçlar')
        
        # İndeks yeniden oluştur
        rebuild_index_action = QAction('🔄 Semantik İndeksi Yeniden Oluştur', self)
        rebuild_index_action.setStatusTip('Tüm belgeler için arama indeksini yeniden oluşturur')
        rebuild_index_action.triggered.connect(self.rebuild_semantic_index)
        tools_menu.addAction(rebuild_index_action)
        
        # Veritabanı bakımı
        vacuum_action = QAction('🗂️ Veritabanı Bakımı', self)
        vacuum_action.setStatusTip('Veritabanını optimize eder ve gereksiz alanları temizler')
        vacuum_action.triggered.connect(self.vacuum_database)
        tools_menu.addAction(vacuum_action)
        
        tools_menu.addSeparator()
        
        # Ayarlar
        settings_action = QAction('⚙️ Ayarlar', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu('❓ Yardım')
        
        # Kullanım Kılavuzu
        help_action = QAction('📚 Kullanım Kılavuzu', self)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        # Hakkında
        about_action = QAction('ℹ️ Hakkında', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Toolbar oluştur"""
        toolbar = self.addToolBar('Ana Araçlar')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # Belge ekleme butonu (ana özellik)
        add_files_action = toolbar.addAction('📄➕ Belge Ekle')
        add_files_action.setStatusTip('Dosya seçerek yeni belge ekle (Ctrl+O)')
        add_files_action.triggered.connect(self.select_and_process_files)
        
        # Raw klasör tarama
        scan_action = toolbar.addAction('� Raw Tara')
        scan_action.setStatusTip('Raw klasörünü otomatik tara')
        scan_action.triggered.connect(self.scan_raw_folder)
        
        toolbar.addSeparator()
        
        # İndeks yeniden oluşturma
        rebuild_action = toolbar.addAction('🔄 İndeksi Yenile')
        rebuild_action.setStatusTip('Arama indeksini yeniden oluştur')
        rebuild_action.triggered.connect(self.rebuild_semantic_index)
        
        toolbar.addSeparator()
        
        # Ayarlar
        settings_action = toolbar.addAction('⚙️ Ayarlar')
        settings_action.triggered.connect(self.open_settings)
    
    def create_left_panel(self) -> QWidget:
        """Sol panel - belge ağacı ve filtreler"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Başlık
        title_label = QLabel("Belgeler ve Filtreler")
        title_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(title_label)
        
        # Belge ağacı
        self.document_tree = DocumentTreeContainer(self.db)
        self.document_tree.document_selected.connect(self.on_document_selected)
        layout.addWidget(self.document_tree)
        
        # Filtre grubu
        filter_group = QGroupBox("Filtreler")
        filter_layout = QVBoxLayout(filter_group)
        
        # Belge türü filtresi
        filter_layout.addWidget(QLabel("Belge Türü:"))
        self.document_type_combo = QComboBox()
        self.document_type_combo.addItems([
            "Tümü", "ANAYASA", "KANUN", "KHK", "TÜZÜK", 
            "YÖNETMELİK", "YÖNERGE", "TEBLİĞ", "KARAR"
        ])
        self.document_type_combo.currentTextChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.document_type_combo)
        
        # Mülga dahil etme
        self.include_repealed_checkbox = QCheckBox("Mülga maddeleri dahil et")
        self.include_repealed_checkbox.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.include_repealed_checkbox)
        
        # Değişiklik dahil etme
        self.include_amended_checkbox = QCheckBox("Değişiklik içerenleri göster")
        self.include_amended_checkbox.setChecked(True)
        self.include_amended_checkbox.toggled.connect(self.on_filter_changed)
        filter_layout.addWidget(self.include_amended_checkbox)
        
        layout.addWidget(filter_group)
        
        # Favori maddeler
        favorites_group = QGroupBox("Favoriler")
        favorites_layout = QVBoxLayout(favorites_group)
        
        self.favorites_list = QTreeWidget()
        self.favorites_list.setHeaderLabels(["Başlık", "Belge"])
        self.favorites_list.itemDoubleClicked.connect(self.on_favorite_selected)
        favorites_layout.addWidget(self.favorites_list)
        
        # Favori ekleme butonu
        add_favorite_btn = QPushButton("Favori Ekle")
        add_favorite_btn.clicked.connect(self.add_to_favorites)
        favorites_layout.addWidget(add_favorite_btn)
        
        layout.addWidget(favorites_group)
        
        # Son aramalar
        recent_group = QGroupBox("Son Aramalar")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_searches_list = QTreeWidget()
        self.recent_searches_list.setHeaderLabels(["Sorgu", "Tarih"])
        self.recent_searches_list.itemDoubleClicked.connect(self.on_recent_search_selected)
        recent_layout.addWidget(self.recent_searches_list)
        
        layout.addWidget(recent_group)
        
        return panel
    
    def create_middle_panel(self) -> QWidget:
        """Orta panel - arama ve sonuçlar"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Arama widget'ı
        self.search_widget = SearchWidget(self.search_engine)
        self.search_widget.search_requested.connect(self.perform_search)
        layout.addWidget(self.search_widget)
        
        # Sonuç sayısı ve bilgi
        info_layout = QHBoxLayout()
        self.result_count_label = QLabel("Sonuç bulunamadı")
        info_layout.addWidget(self.result_count_label)
        info_layout.addStretch()
        
        # Sıralama seçeneği
        info_layout.addWidget(QLabel("Sıralama:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Relevans", "Tarih (Yeni)", "Tarih (Eski)", "Belge Türü"])
        self.sort_combo.currentTextChanged.connect(self.sort_results)
        info_layout.addWidget(self.sort_combo)
        
        layout.addLayout(info_layout)
        
        # Sonuç widget'ı
        self.result_widget = ResultWidget()
        self.result_widget.result_selected.connect(self.on_result_selected)
        self.result_widget.add_note_requested.connect(self.add_note_to_article)
        layout.addWidget(self.result_widget)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Sağ panel - detay ve istatistikler"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Detay sekmesi
        detail_tab = QWidget()
        detail_layout = QVBoxLayout(detail_tab)
        
        # Detay başlığı
        self.detail_title_label = QLabel("Detay")
        self.detail_title_label.setFont(QFont("", 12, QFont.Bold))
        detail_layout.addWidget(self.detail_title_label)
        
        # Detay içeriği
        self.detail_content = QTextEdit()
        self.detail_content.setReadOnly(True)
        detail_layout.addWidget(self.detail_content)
        
        # Not ekleme alanı
        notes_group = QGroupBox("Notlar")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_text)
        
        notes_btn_layout = QHBoxLayout()
        save_note_btn = QPushButton("Not Kaydet")
        save_note_btn.clicked.connect(self.save_note)
        notes_btn_layout.addWidget(save_note_btn)
        
        clear_note_btn = QPushButton("Temizle")
        clear_note_btn.clicked.connect(lambda: self.notes_text.clear())
        notes_btn_layout.addWidget(clear_note_btn)
        
        notes_layout.addLayout(notes_btn_layout)
        detail_layout.addWidget(notes_group)
        
        tab_widget.addTab(detail_tab, "Detay")
        
        # Belge Görüntüleme sekmesi
        viewer_tab = QWidget()
        viewer_layout = QVBoxLayout(viewer_tab)
        
        # Tab seçimi
        viewer_tab_selector = QTabWidget()
        
        # PDF Viewer sekmesi
        pdf_viewer_tab = QWidget()
        pdf_viewer_layout = QVBoxLayout(pdf_viewer_tab)
        
        from .pdf_viewer_widget import PDFViewerWidget
        self.pdf_viewer = PDFViewerWidget()
        self.pdf_viewer.document_loaded.connect(self.on_pdf_document_loaded)
        pdf_viewer_layout.addWidget(self.pdf_viewer)
        
        viewer_tab_selector.addTab(pdf_viewer_tab, "📄 PDF Görüntüleyici")
        
        # Document Preview sekmesi
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        from .document_preview_widget import DocumentPreviewWidget
        self.document_preview = DocumentPreviewWidget()
        self.document_preview.document_selected.connect(self.on_preview_document_selected)
        self.document_preview.text_selected.connect(self.on_preview_text_selected)
        preview_layout.addWidget(self.document_preview)
        
        viewer_tab_selector.addTab(preview_tab, "📝 Metin Önizleme")
        
        viewer_layout.addWidget(viewer_tab_selector)
        tab_widget.addTab(viewer_tab, "🔍 Belge Görüntüleme")
        
        # İstatistik sekmesi
        self.stats_widget = StatsWidget(self.db, self.search_engine)
        tab_widget.addTab(self.stats_widget, "İstatistikler")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def create_status_bar(self):
        """Status bar oluştur"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # File watcher status
        self.file_watcher_status = FileWatcherStatus()
        self.status_bar.addPermanentWidget(self.file_watcher_status)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Ana klasör gösterimi
        base_folder = self.config.get('base_folder', '')
        self.status_bar.showMessage(f"Ana Klasör: {base_folder}")
    
    def apply_theme(self):
        """Tema uygula"""
        theme = self.config.get('preferences.theme', 'system')
        
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    color: #ffffff;
                    padding: 5px;
                }
                QPushButton {
                    background-color: #0078d4;
                    border: none;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QTreeWidget, QTableWidget {
                    background-color: #3c3c3c;
                    alternate-background-color: #404040;
                    border: 1px solid #555555;
                }
            """)
    
    def load_settings(self):
        """Ayarları yükle"""
        try:
            # Pencere pozisyonu ve boyutu
            if self.config.get('preferences.save_window_position', True):
                self._load_window_position()
            
            # Font boyutu
            font_size = self.config.get('preferences.font_size', 'medium')
            if font_size == 'large':
                font = self.font()
                font.setPointSize(font.pointSize() + 2)
                self.setFont(font)
            elif font_size == 'small':
                font = self.font()
                font.setPointSize(font.pointSize() - 1)
                self.setFont(font)
            
            # Tema ayarları
            theme = self.config.get('preferences.theme', 'default')
            self.apply_theme(theme)
            
            # Dil ayarları
            language = self.config.get('preferences.language', 'tr')
            self.apply_language(language)
            
            # Arama ayarları
            self._load_search_settings()
            
        except Exception as e:
            self.logger.error(f"Ayarlar yükleme hatası: {e}")
    
    def _load_window_position(self):
        """Pencere pozisyonunu yükle"""
        try:
            pos_x = self.config.get('window.position.x', None)
            pos_y = self.config.get('window.position.y', None)
            width = self.config.get('window.size.width', None)
            height = self.config.get('window.size.height', None)
            
            if all(v is not None for v in [pos_x, pos_y, width, height]):
                # Ekran sınırları içinde mi kontrol et
                screen = QApplication.primaryScreen().geometry()
                if (0 <= pos_x <= screen.width() - 100 and 
                    0 <= pos_y <= screen.height() - 100):
                    self.move(pos_x, pos_y)
                    self.resize(width, height)
                else:
                    # Ekran dışındaysa merkeze al
                    self.center_window()
            else:
                # Pozisyon yoksa merkeze al
                self.center_window()
                
        except Exception as e:
            self.logger.error(f"Pencere pozisyonu yükleme hatası: {e}")
            self.center_window()
    
    def center_window(self):
        """Pencereyi ekranın merkezine al"""
        try:
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        except Exception as e:
            self.logger.error(f"Pencere merkezleme hatası: {e}")
    
    def _load_search_settings(self):
        """Arama ayarlarını yükle"""
        try:
            # Maksimum sonuç sayısı
            max_results = self.config.get('search.max_results', 20)
            if hasattr(self, 'result_widget'):
                self.result_widget.set_max_results(max_results)
            
            # Arama geçmişi
            search_history = self.config.get('search.history', [])
            if hasattr(self, 'search_widget') and search_history:
                self.search_widget.set_search_history(search_history)
                
        except Exception as e:
            self.logger.error(f"Arama ayarları yükleme hatası: {e}")
    
    def apply_theme(self, theme_name: str):
        """Tema uygula"""
        try:
            if theme_name == 'dark':
                self._apply_dark_theme()
            elif theme_name == 'light':
                self._apply_light_theme()
            else:
                self._apply_default_theme()
        except Exception as e:
            self.logger.error(f"Tema uygulama hatası: {e}")
    
    def apply_language(self, language: str):
        """Dil ayarlarını uygula"""
        try:
            # Dil değişikliği için gerekli işlemler
            if language == 'en':
                self._translate_to_english()
            else:
                self._translate_to_turkish()
        except Exception as e:
            self.logger.error(f"Dil uygulama hatası: {e}")
    
    def _apply_dark_theme(self):
        """Koyu tema uygula"""
        try:
            dark_style = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #4a4a4a;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #4a4a4a;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4a4a4a;
            }
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
            }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555555;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            """
            self.setStyleSheet(dark_style)
            self.logger.info("Koyu tema uygulandı")
            
        except Exception as e:
            self.logger.error(f"Koyu tema uygulama hatası: {e}")
    
    def _apply_light_theme(self):
        """Açık tema uygula"""
        try:
            light_style = """
            QMainWindow {
                background-color: #f5f5f5;
                color: #333333;
            }
            QWidget {
                background-color: #f5f5f5;
                color: #333333;
            }
            QMenuBar {
                background-color: #ffffff;
                color: #333333;
                border-bottom: 1px solid #cccccc;
            }
            QMenuBar::item:selected {
                background-color: #e6e6e6;
            }
            QMenu {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
            }
            QMenu::item:selected {
                background-color: #e6e6e6;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #cccccc;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            QTableWidget {
                background-color: #ffffff;
                color: #333333;
                gridline-color: #cccccc;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #333333;
                padding: 4px;
                border: 1px solid #cccccc;
            }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 4px;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            """
            self.setStyleSheet(light_style)
            self.logger.info("Açık tema uygulandı")
            
        except Exception as e:
            self.logger.error(f"Açık tema uygulama hatası: {e}")
    
    def _apply_default_theme(self):
        """Varsayılan tema uygula"""
        try:
            self.setStyleSheet("")
            self.logger.info("Varsayılan tema uygulandı")
            
        except Exception as e:
            self.logger.error(f"Varsayılan tema uygulama hatası: {e}")
    
    def _translate_to_english(self):
        """İngilizce'ye çevir"""
        try:
            # UI metinlerini İngilizce'ye çevir
            self.setWindowTitle("Legal Document Analysis System")
            # Diğer çeviriler...
            self.logger.info("Dil İngilizce'ye çevrildi")
            
        except Exception as e:
            self.logger.error(f"İngilizce çeviri hatası: {e}")
    
    def _translate_to_turkish(self):
        """Türkçe'ye çevir"""
        try:
            # UI metinlerini Türkçe'ye çevir
            self.setWindowTitle("Mevzuat Belge Analiz Sistemi")
            # Diğer çeviriler...
            self.logger.info("Dil Türkçe'ye çevrildi")
            
        except Exception as e:
            self.logger.error(f"Türkçe çeviri hatası: {e}")
    
    def perform_search(self, query: str, search_type: str):
        """Arama gerçekleştir"""
        if not query.strip():
            return
        
        self.status_bar.showMessage("Arama yapılıyor...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        try:
            # Filtreleri al
            document_types = []
            selected_type = self.document_type_combo.currentText()
            if selected_type != "Tümü":
                document_types = [selected_type]
            
            include_repealed = self.include_repealed_checkbox.isChecked()
            
            # Arama yap
            results = self.search_engine.search(
                query=query,
                document_types=document_types,
                search_type=search_type,
                include_repealed=include_repealed
            )
            
            self.last_search_results = results
            
            # Sonuçları göster
            self.result_widget.display_results(results)
            
            # Sonuç sayısını güncelle
            self.result_count_label.setText(f"{len(results)} sonuç bulundu")
            
            # Status
            self.status_bar.showMessage(f"Arama tamamlandı: {len(results)} sonuç")
            
        except Exception as e:
            self.logger.error(f"Arama hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Arama sırasında hata oluştu:\n{e}")
            self.status_bar.showMessage("Arama başarısız")
        
        finally:
            self.progress_bar.setVisible(False)
    
    def sort_results(self, sort_type: str):
        """Sonuçları sırala"""
        if not self.last_search_results:
            return
        
        if sort_type == "Relevans":
            self.last_search_results.sort(key=lambda x: x.score, reverse=True)
        elif sort_type == "Tarih (Yeni)":
            self._sort_by_date_newest_first()
        elif sort_type == "Tarih (Eski)":
            self._sort_by_date_oldest_first()
        elif sort_type == "Belge Türü":
            self.last_search_results.sort(key=lambda x: x.document_type)
        
        self.result_widget.display_results(self.last_search_results)
    
    def _sort_by_date_newest_first(self):
        """Sonuçları tarihe göre yeniden eskiye sırala"""
        try:
            # Tarih bilgisi olan sonuçları önce sırala
            dated_results = []
            undated_results = []
            
            for result in self.last_search_results:
                if hasattr(result, 'document_date') and result.document_date:
                    dated_results.append(result)
                else:
                    undated_results.append(result)
            
            # Tarihli sonuçları yeniden eskiye sırala
            dated_results.sort(key=lambda x: x.document_date, reverse=True)
            
            # Tarihsiz sonuçları sona ekle
            self.last_search_results = dated_results + undated_results
            
        except Exception as e:
            self.logger.error(f"Tarih sıralama hatası (yeni): {e}")
            # Hata durumunda orijinal sırayı koru
    
    def _sort_by_date_oldest_first(self):
        """Sonuçları tarihe göre eskiden yeniye sırala"""
        try:
            # Tarih bilgisi olan sonuçları önce sırala
            dated_results = []
            undated_results = []
            
            for result in self.last_search_results:
                if hasattr(result, 'document_date') and result.document_date:
                    dated_results.append(result)
                else:
                    undated_results.append(result)
            
            # Tarihli sonuçları eskiden yeniye sırala
            dated_results.sort(key=lambda x: x.document_date, reverse=False)
            
            # Tarihsiz sonuçları sona ekle
            self.last_search_results = dated_results + undated_results
            
        except Exception as e:
            self.logger.error(f"Tarih sıralama hatası (eski): {e}")
            # Hata durumunda orijinal sırayı koru
    
    def on_result_selected(self, result: SearchResult):
        """Sonuç seçildiğinde"""
        self.display_article_detail(result)
    
    def display_article_detail(self, result: SearchResult):
        """Madde detayını göster"""
        # Aktif madde ID'sini sakla
        self.current_article_id = result.id
        
        # Başlık
        title = f"{result.document_title}"
        if result.law_number:
            title += f" (Kanun No: {result.law_number})"
        if result.article_number:
            title += f" - Madde {result.article_number}"
        
        self.detail_title_label.setText(title)
        
        # İçerik
        content = f"<h3>{result.title}</h3>\n" if result.title else ""
        content += f"<p>{result.content}</p>"
        
        # Highlight'ları ekle
        if result.highlights:
            content += "<h4>İlgili Bölümler:</h4>"
            for highlight in result.highlights:
                content += f"<p><i>...{highlight}...</i></p>"
        
        # Meta bilgiler
        content += "<hr><h4>Belge Bilgileri:</h4>"
        content += f"<p><strong>Tür:</strong> {result.document_type}</p>"
        if result.law_number:
            content += f"<p><strong>Kanun Numarası:</strong> {result.law_number}</p>"
        content += f"<p><strong>Durum:</strong> "
        if result.is_repealed:
            content += "Mülga"
        elif result.is_amended:
            content += "Değişiklik var"
        else:
            content += "Aktif"
        content += "</p>"
        content += f"<p><strong>Skor:</strong> {result.score:.3f} ({result.match_type})</p>"
        
        self.detail_content.setHtml(content)
        
        # Mevcut notları yükle
        self.load_article_notes(result.id)
    
    def load_article_notes(self, article_id: int):
        """Madde notlarını yükle"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT content FROM user_notes 
                WHERE article_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (article_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                self.notes_text.setPlainText(result[0])
            else:
                self.notes_text.clear()
                
        except Exception as e:
            self.logger.error(f"Not yükleme hatası: {e}")
    
    def save_note(self):
        """Not kaydet"""
        if not hasattr(self, 'current_article_id'):
            QMessageBox.information(self, "Bilgi", "Önce bir madde seçin")
            return
        
        note_content = self.notes_text.toPlainText().strip()
        if not note_content:
            return
        
        try:
            from datetime import datetime
            
            with self.db.transaction() as cursor:
                # Mevcut notu kontrol et
                cursor.execute("""
                    SELECT id FROM user_notes WHERE article_id = ?
                """, (self.current_article_id,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Güncelle
                    cursor.execute("""
                        UPDATE user_notes 
                        SET content = ?, updated_at = ?
                        WHERE article_id = ?
                    """, (note_content, datetime.now().isoformat(), self.current_article_id))
                else:
                    # Yeni ekle
                    cursor.execute("""
                        INSERT INTO user_notes (article_id, content, created_at)
                        VALUES (?, ?, ?)
                    """, (self.current_article_id, note_content, datetime.now().isoformat()))
            
            self.status_bar.showMessage("Not kaydedildi", 3000)
            
        except Exception as e:
            self.logger.error(f"Not kaydetme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Not kaydedilirken hata oluştu:\n{e}")
    
    def on_document_selected(self, document_data: dict):
        """Belge seçildiğinde"""
        try:
            self.logger.info(f"Belge seçildi: {document_data.get('title', 'Bilinmeyen')}")
            
            self.current_document = document_data
            
            # Detay panelini güncelle
            self.update_detail_panel(document_data)
            
            # Sonuçları temizle
            if hasattr(self, 'result_widget'):
                self.result_widget.clear_results()
            
            # Belgeyi viewer'da yükle
            self.load_document_in_viewer(document_data)
            
        except Exception as e:
            self.logger.error(f"Belge seçim hatası: {e}")
    
    def update_detail_panel(self, document_data: dict):
        """Detay panelini güncelle"""
        try:
            if not document_data:
                return
                
            # Başlık
            title = document_data.get('title', 'Başlık yok')
            self.detail_title_label.setText(title)
            
            # İçerik
            content = document_data.get('content', 'İçerik yok')
            if len(content) > 1000:
                content = content[:1000] + "...\n\n[İçerik kısaltıldı - tamamını görmek için belge görüntüleyiciyi kullanın]"
            
            self.detail_content.setPlainText(content)
            
            # Notları yükle
            self.load_notes_for_document(document_data.get('id'))
            
        except Exception as e:
            self.logger.error(f"Detay panel güncelleme hatası: {e}")
    
    def load_notes_for_document(self, document_id: int):
        """Belge için notları yükle"""
        try:
            if not document_id:
                self.notes_text.clear()
                return
                
            # Veritabanından notları al
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT content, created_at FROM user_notes 
                WHERE article_id IN (
                    SELECT id FROM articles WHERE document_id = ?
                ) ORDER BY created_at DESC
            """, (document_id,))
            
            notes = cursor.fetchall()
            cursor.close()
            
            if notes:
                notes_text = "\n\n".join([
                    f"[{note[1][:10]}] {note[0]}"
                    for note in notes
                ])
                self.notes_text.setPlainText(notes_text)
            else:
                self.notes_text.clear()
                
        except Exception as e:
            self.logger.error(f"Not yükleme hatası: {e}")
            self.notes_text.clear()
    
    def on_filter_changed(self):
        """Filtre değiştiğinde"""
        # Eğer aktif arama varsa yeniden çalıştır
        if hasattr(self.search_widget, 'last_query') and self.search_widget.last_query:
            self.perform_search(self.search_widget.last_query, self.search_widget.last_search_type)
    
    def manual_scan(self):
        """Manuel tarama başlat - dosya seçimi veya raw klasör taraması"""
        # İki seçenek sun: Dosya seçimi veya raw klasör taraması
        reply = QMessageBox.question(
            self, "Belge Ekleme Seçimi",
            "Belge ekleme yöntemini seçin:\n\n" +
            "YES: Dosya seçerek ekle\n" +
            "NO: Raw klasörünü tara\n" +
            "CANCEL: İptal",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            # Dosya seçim dialog'u
            self.select_and_process_files()
        elif reply == QMessageBox.No:
            # Raw klasör taraması
            self.scan_raw_folder()
        # Cancel ise hiçbir şey yapma
    
    def select_and_process_files(self):
        """Dosya seçim dialog'u ile belge ekleme"""
        try:
            files, _ = QFileDialog.getOpenFileNames(
                self, 
                "Mevzuat Belgelerini Seçin",
                "",
                "Desteklenen Dosyalar (*.pdf *.docx *.doc *.txt);;PDF Dosyaları (*.pdf);;Word Dosyaları (*.docx *.doc);;Metin Dosyaları (*.txt);;Tüm Dosyalar (*)"
            )
            
            if not files:
                return
            
            # Progress bar göster
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(files))
            
            processed_count = 0
            failed_files = []
            
            for i, file_path in enumerate(files):
                self.progress_bar.setValue(i)
                self.status_bar.showMessage(f"İşleniyor: {Path(file_path).name}")
                QApplication.processEvents()  # UI'yı güncelle
                
                try:
                    # Dosyayı doğrudan işle
                    result = self.document_processor.process_file(file_path)
                    
                    if result['success']:
                        processed_count += 1
                        self.logger.info(f"Dosya başarıyla eklendi: {file_path}")
                    else:
                        failed_files.append(f"{Path(file_path).name}: {result.get('error', 'Bilinmeyen hata')}")
                        self.logger.error(f"Dosya ekleme başarısız: {file_path} - {result.get('error')}")
                        
                except Exception as e:
                    failed_files.append(f"{Path(file_path).name}: {str(e)}")
                    self.logger.error(f"Dosya işleme exception: {file_path} - {e}")
            
            # Sonucu göster
            self.progress_bar.setVisible(False)
            
            if failed_files:
                error_msg = f"İşlem tamamlandı:\n\n" +\
                           f"Başarılı: {processed_count} dosya\n" +\
                           f"Başarısız: {len(failed_files)} dosya\n\n" +\
                           "Başarısız dosyalar:\n" + "\n".join(failed_files[:10])
                if len(failed_files) > 10:
                    error_msg += f"\n... ve {len(failed_files)-10} dosya daha"
                    
                QMessageBox.warning(self, "Belge Ekleme Sonucu", error_msg)
            else:
                QMessageBox.information(
                    self, "Başarılı", 
                    f"Tüm dosyalar başarıyla eklendi!\n\nToplam: {processed_count} dosya"
                )
            
            # Belge ağacını yenile
            self.document_tree.refresh_tree()
            self.stats_widget.refresh_stats()
            self.status_bar.showMessage(f"Belge ekleme tamamlandı: {processed_count} başarılı", 5000)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.logger.error(f"Dosya seçimi hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Dosya seçimi sırasında hata oluştu:\n{e}")
    
    def scan_raw_folder(self):
        """Raw klasörünü tara"""
        if not self.file_watcher:
            QMessageBox.information(self, "Bilgi", "File Watcher aktif değil")
            return
        
        reply = QMessageBox.question(
            self, "Raw Klasör Tarama",
            "Raw klasöründeki işlenmemiş dosyalar taranacak. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                files_added = self.file_watcher.manual_scan()
                QMessageBox.information(
                    self, "Manuel Tarama",
                    f"Tarama tamamlandı. {files_added} dosya işleme kuyruğuna eklendi."
                )
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Manuel tarama hatası:\n{e}")
    
    def rebuild_semantic_index(self):
        """Semantik indeksi yeniden oluştur"""
        reply = QMessageBox.question(
            self, "İndeks Yenileme",
            "Tüm semantik indeks yeniden oluşturulacak. Bu işlem uzun sürebilir. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.status_bar.showMessage("Semantik indeks yeniden oluşturuluyor...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            try:
                success = self.search_engine.rebuild_index()
                if success:
                    QMessageBox.information(self, "Başarılı", "Semantik indeks yeniden oluşturuldu")
                    self.status_bar.showMessage("İndeks yenileme tamamlandı", 3000)
                else:
                    QMessageBox.warning(self, "Uyarı", "İndeks yenileme sırasında sorunlar oluştu")
                    self.status_bar.showMessage("İndeks yenileme başarısız", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"İndeks yenileme hatası:\n{e}")
                self.status_bar.showMessage("İndeks yenileme hatası", 3000)
            finally:
                self.progress_bar.setVisible(False)
    
    def vacuum_database(self):
        """Veritabanı bakımı"""
        reply = QMessageBox.question(
            self, "Veritabanı Bakımı",
            "Veritabanı bakımı yapılacak. Bu işlem birkaç dakika sürebilir. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.status_bar.showMessage("Veritabanı bakımı yapılıyor...")
                self.db.vacuum()
                QMessageBox.information(self, "Başarılı", "Veritabanı bakımı tamamlandı")
                self.status_bar.showMessage("Veritabanı bakımı tamamlandı", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Veritabanı bakım hatası:\n{e}")
    
    def export_results(self):
        """Sonuçları PDF'e aktar"""
        if not self.last_search_results:
            QMessageBox.information(self, "Bilgi", "Dışa aktarılacak sonuç bulunamadı")
            return
        
        # Dosya adı seç
        filename, _ = QFileDialog.getSaveFileName(
            self, "PDF Rapor Kaydet", 
            f"arama_sonuclari_{int(time.time())}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                # TODO: Implement PDF export
                QMessageBox.information(self, "Başarılı", f"Sonuçlar {filename} dosyasına kaydedildi")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"PDF export hatası:\n{e}")
    
    def open_settings(self):
        """Ayarlar penceresini aç"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == SettingsDialog.Accepted:
            # Ayarlar değişti, UI'yi güncelle
            self.apply_theme()
            # File watcher'ı restart et (gerekiyorsa)
            # TODO: Implement settings application
    
    def update_status(self):
        """Durumu güncelle"""
        try:
            # File watcher durumu
            if self.file_watcher:
                status = self.file_watcher.get_status()
                self.file_watcher_status.update_status(
                    status['is_watching'],
                    status['queue_size']
                )
            
            # İstatistikleri güncelle
            if hasattr(self, 'stats_widget'):
                self.stats_widget.refresh_stats()
            
        except Exception as e:
            self.logger.error(f"Status güncelleme hatası: {e}")
    
    def show_help(self):
        """Kullanım kılavuzu göster"""
        help_text = """
        <h2>📚 Mevzuat Sistemi Kullanım Kılavuzu</h2>
        
        <h3>🔹 Belge Ekleme Yöntemleri:</h3>
        <ul>
        <li><b>Dosya Seçimi (Önerilen):</b> Menü > Dosya > "Dosya Seçerek Belge Ekle" veya Ctrl+O</li>
        <li><b>Drag & Drop:</b> Dosyaları doğrudan ana pencereye sürükleyip bırakın</li>
        <li><b>Raw Klasör Tarama:</b> Raw klasörüne dosya koyup "Raw Klasörü Tara" butonunu kullanın</li>
        </ul>
        
        <h3>🔹 Desteklenen Dosya Türleri:</h3>
        <ul>
        <li>📄 PDF dosyaları (.pdf)</li>
        <li>📝 Word belgeleri (.docx, .doc)</li>
        <li>📋 Metin dosyaları (.txt)</li>
        </ul>
        
        <h3>🔹 Arama Özellikleri:</h3>
        <ul>
        <li><b>Semantik Arama:</b> Anlamsal benzerlik ile arama</li>
        <li><b>Anahtar Kelime:</b> Klasik kelime bazlı arama</li>
        <li><b>Karma Arama:</b> Her iki yöntemin kombinasyonu</li>
        <li><b>Filtreler:</b> Belge türü, mülga/aktif durumu filtreleme</li>
        </ul>
        
        <h3>🔹 İpuçları:</h3>
        <ul>
        <li>Dosya ekleme öncesi duplicate kontrol yapılır</li>
        <li>Minimum 50 karakter metin gerekliliği vardır</li>
        <li>Maksimum dosya boyutu: 50MB</li>
        <li>İndeksi düzenli olarak yenileyin (🔄)</li>
        <li>Favoriler ve notlar ekleyebilirsiniz</li>
        </ul>
        
        <h3>🔹 Sorun Giderme:</h3>
        <ul>
        <li><b>Dosya eklenmiyor:</b> Dosya boyutunu ve türünü kontrol edin</li>
        <li><b>Arama sonuç vermez:</b> İndeksi yenileyin</li>
        <li><b>Yavaş çalışma:</b> Veritabanı bakımı yapın</li>
        </ul>
        """
        
        QMessageBox.about(self, "Kullanım Kılavuzu", help_text)
    
    def show_about(self):
        """Hakkında dialog'u göster"""
        about_text = f"""
        <h2>Mevzuat Belge Analiz & Sorgulama Sistemi</h2>
        <p><b>Versiyon:</b> {self.config.get('app_version', '1.0.2')}</p>
        <p><b>Oluşturma Tarihi:</b> {self.config.get('creation_date', '')}</p>
        <p><b>Kullanıcı:</b> {self.config.get('user_id', '')}</p>
        <hr>
        <p>Bu yazılım mevzuat belgelerini otomatik olarak işleyip</p>
        <p>sorgulama imkanı sunan bir masaüstü uygulamasıdır.</p>
        <hr>
        <p><b>Ana Klasör:</b> {self.config.get('base_folder', '')}</p>
        <p><b>Veritabanı:</b> {self.config.get_db_path()}</p>
        """
        
        QMessageBox.about(self, "Hakkında", about_text)
    
    def on_favorite_selected(self, item, column):
        """Favori seçildiğinde"""
        try:
            # Favori item'dan madde bilgilerini al
            article_id = item.data(0, Qt.UserRole)
            if article_id:
                # Maddeyi veritabanından getir
                cursor = self.db.connection.cursor()
                cursor.execute("""
                    SELECT a.*, d.title as document_title, d.law_number, d.document_type
                    FROM articles a
                    JOIN documents d ON a.document_id = d.id
                    WHERE a.id = ?
                """, (article_id,))
                
                result = cursor.fetchone()
                cursor.close()
                
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    article_data = dict(zip(columns, result))
                    
                    # SearchResult benzeri obje oluştur
                    from ..core.search_engine import SearchResult
                    search_result = SearchResult(
                        id=article_data['id'],
                        document_id=article_data['document_id'],
                        document_title=article_data['document_title'],
                        law_number=article_data.get('law_number', ''),
                        document_type=article_data['document_type'],
                        article_number=article_data.get('article_number', ''),
                        title=article_data.get('title', ''),
                        content=article_data['content'],
                        score=1.0,
                        match_type="favorite",
                        is_repealed=article_data.get('is_repealed', False),
                        is_amended=article_data.get('is_amended', False)
                    )
                    
                    self.display_article_detail(search_result)
                    
        except Exception as e:
            self.logger.error(f"Favori seçim hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Favori açılırken hata oluştu:\n{e}")
    
    def on_recent_search_selected(self, item, column):
        """Son arama seçildiğinde"""
        try:
            query = item.text(0)
            if query:
                # Arama widget'ına sorguyu yükle ve çalıştır
                self.search_widget.set_query(query)
                self.perform_search(query, "mixed")
                
        except Exception as e:
            self.logger.error(f"Son arama seçim hatası: {e}")
    
    def add_to_favorites(self):
        """Aktif maddeyi favorilere ekle"""
        if not hasattr(self, 'current_article_id') or not self.current_article_id:
            QMessageBox.information(self, "Bilgi", "Önce bir madde seçin")
            return
        
        try:
            # Madde bilgilerini al
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT a.title, a.article_number, d.title as document_title
                FROM articles a
                JOIN documents d ON a.document_id = d.id
                WHERE a.id = ?
            """, (self.current_article_id,))
            
            result = cursor.fetchone()
            
            if result:
                title = result[0] or f"Madde {result[1] or ''}"
                document_title = result[2]
                
                # Favorilerde var mı kontrol et
                cursor.execute("""
                    SELECT id FROM favorites WHERE article_id = ?
                """, (self.current_article_id,))
                
                if cursor.fetchone():
                    QMessageBox.information(self, "Bilgi", "Bu madde zaten favorilerinizde")
                    cursor.close()
                    return
                
                # Favoriye ekle
                cursor.execute("""
                    INSERT INTO favorites (article_id, title, created_at)
                    VALUES (?, ?, ?)
                """, (self.current_article_id, f"{title} ({document_title})", datetime.now().isoformat()))
                
                self.db.connection.commit()
                cursor.close()
                
                # Favori listesini güncelle
                self.refresh_favorites()
                
                self.status_bar.showMessage("Favoriye eklendi", 3000)
                
            else:
                cursor.close()
                QMessageBox.warning(self, "Uyarı", "Madde bilgisi bulunamadı")
                
        except Exception as e:
            self.logger.error(f"Favori ekleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Favori eklenirken hata oluştu:\n{e}")
    
    def refresh_favorites(self):
        """Favori listesini güncelle"""
        try:
            self.favorites_list.clear()
            
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT f.article_id, f.title, d.title as document_title
                FROM favorites f
                JOIN articles a ON f.article_id = a.id
                JOIN documents d ON a.document_id = d.id
                ORDER BY f.created_at DESC
            """)
            
            for row in cursor.fetchall():
                item = QTreeWidgetItem([row[1], row[2]])
                item.setData(0, Qt.UserRole, row[0])  # article_id'yi sakla
                self.favorites_list.addTopLevelItem(item)
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"Favori listesi yenileme hatası: {e}")
    
    def add_note_to_article(self, article_id: int, note: str):
        """Maddeye not ekle"""
        try:
            with self.db.transaction() as cursor:
                cursor.execute("""
                    INSERT INTO user_notes (article_id, content, created_at)
                    VALUES (?, ?, ?)
                """, (article_id, note, datetime.now().isoformat()))
            
            self.logger.info(f"Not eklendi: article_id={article_id}")
            
        except Exception as e:
            self.logger.error(f"Not ekleme hatası: {e}")
            raise
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Drag enter event - dosya sürüklendiğinde"""
        if event.mimeData().hasUrls():
            # Sadece desteklenen dosya türlerini kabul et
            urls = event.mimeData().urls()
            supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
            
            valid_files = []
            for url in urls:
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.suffix.lower() in supported_extensions:
                        valid_files.append(file_path)
            
            if valid_files:
                event.acceptProposedAction()
                # Visual feedback
                self.status_bar.showMessage(f"{len(valid_files)} desteklenen dosya algılandı")
            else:
                event.ignore()
                self.status_bar.showMessage("Desteklenmeyen dosya türü")
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Drag leave event - sürükleme bırakıldığında"""
        self.status_bar.clearMessage()
        event.accept()
    
    def dropEvent(self, event: QDropEvent):
        """Drop event - dosya bırakıldığında"""
        try:
            urls = event.mimeData().urls()
            supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
            
            valid_files = []
            for url in urls:
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.suffix.lower() in supported_extensions:
                        valid_files.append(str(file_path))
            
            if valid_files:
                event.acceptProposedAction()
                
                # Onay dialog'u göster
                reply = QMessageBox.question(
                    self, "Dosya Ekleme Onayı",
                    f"{len(valid_files)} dosya sisteme eklenecek. Devam edilsin mi?\n\n" + 
                    "\n".join([Path(f).name for f in valid_files[:5]]) + 
                    (f"\n... ve {len(valid_files)-5} dosya daha" if len(valid_files) > 5 else ""),
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Dosyaları işle
                    self.process_dropped_files(valid_files)
            else:
                event.ignore()
                QMessageBox.information(self, "Bilgi", "Desteklenmeyen dosya türü")
                
        except Exception as e:
            self.logger.error(f"Drop event hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Dosya ekleme sırasında hata oluştu:\n{e}")
    
    def on_pdf_document_loaded(self, file_path: str):
        """PDF döküman yüklendiğinde"""
        try:
            self.logger.info(f"PDF döküman yüklendi: {file_path}")
            self.status_bar.showMessage(f"PDF yüklendi: {Path(file_path).name}")
            
            # Belge bilgilerini güncelle
            self.update_document_info_for_viewer(file_path)
            
        except Exception as e:
            self.logger.error(f"PDF döküman yükleme hatası: {e}")
            
    def on_preview_document_selected(self, document_data: dict):
        """Preview'da belge seçildiğinde"""
        try:
            self.logger.info(f"Preview'da belge seçildi: {document_data.get('title', 'Bilinmeyen')}")
            
            # Detay panelini güncelle
            self.update_detail_panel(document_data)
            
        except Exception as e:
            self.logger.error(f"Preview belge seçim hatası: {e}")
            
    def on_preview_text_selected(self, selected_text: str):
        """Preview'da metin seçildiğinde"""
        try:
            self.logger.info(f"Preview'da metin seçildi: {len(selected_text)} karakter")
            
            # Seçili metni clipboard'a kopyala
            clipboard = self.clipboard()
            clipboard.setText(selected_text)
            
            # Status bar'da bilgi göster
            self.status_bar.showMessage(f"Metin kopyalandı: {len(selected_text)} karakter")
            
        except Exception as e:
            self.logger.error(f"Preview metin seçim hatası: {e}")
            
    def update_document_info_for_viewer(self, file_path: str):
        """Viewer için belge bilgilerini güncelle"""
        try:
            # Dosya bilgilerini al
            file_info = Path(file_path).stat()
            
            # Belge bilgilerini güncelle
            info_text = f"""
            <b>Dosya:</b> {Path(file_path).name}<br>
            <b>Boyut:</b> {file_info.st_size / 1024:.1f} KB<br>
            <b>Oluşturulma:</b> {datetime.fromtimestamp(file_info.st_ctime).strftime('%d.%m.%Y %H:%M')}<br>
            <b>Son Değişiklik:</b> {datetime.fromtimestamp(file_info.st_mtime).strftime('%d.%m.%Y %H:%M')}
            """
            
            # Detay panelini güncelle
            self.detail_title_label.setText(f"PDF Görüntüleyici - {Path(file_path).name}")
            self.detail_content.setHtml(info_text)
            
        except Exception as e:
            self.logger.error(f"Belge bilgileri güncelleme hatası: {e}")
            
    def load_document_in_viewer(self, document_data: dict):
        """Belgeyi viewer'da yükle"""
        try:
            if not document_data:
                return
                
            file_path = document_data.get('file_path')
            if not file_path or not Path(file_path).exists():
                self.logger.warning(f"Belge dosyası bulunamadı: {file_path}")
                return
                
            # PDF viewer'da yükle
            if hasattr(self, 'pdf_viewer'):
                self.pdf_viewer.load_pdf(file_path)
                
            # Document preview'da yükle
            if hasattr(self, 'document_preview'):
                self.document_preview.load_document(document_data)
                
            # Tab'ı belge görüntüleme sekmesine geçir
            if hasattr(self, 'tab_widget'):
                self.tab_widget.setCurrentIndex(2)  # Belge Görüntüleme sekmesi
                
            self.logger.info(f"Belge viewer'da yüklendi: {document_data.get('title', 'Bilinmeyen')}")
            
        except Exception as e:
            self.logger.error(f"Belge viewer yükleme hatası: {e}")
            
    def process_dropped_files(self, file_paths: List[str]):
        """Drag & drop ile eklenen dosyaları işle"""
        try:
            # Progress bar göster
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, len(file_paths))
            
            processed_count = 0
            failed_files = []
            
            for i, file_path in enumerate(file_paths):
                self.progress_bar.setValue(i)
                self.status_bar.showMessage(f"İşleniyor: {Path(file_path).name}")
                QApplication.processEvents()  # UI'yı güncelle
                
                try:
                    # Dosyayı doğrudan işle
                    result = self.document_processor.process_file(file_path)
                    
                    if result['success']:
                        processed_count += 1
                        self.logger.info(f"Dosya başarıyla eklendi (D&D): {file_path}")
                    else:
                        failed_files.append(f"{Path(file_path).name}: {result.get('error', 'Bilinmeyen hata')}")
                        self.logger.error(f"Dosya ekleme başarısız (D&D): {file_path} - {result.get('error')}")
                        
                except Exception as e:
                    failed_files.append(f"{Path(file_path).name}: {str(e)}")
                    self.logger.error(f"Dosya işleme exception (D&D): {file_path} - {e}")
            
            # Sonucu göster
            self.progress_bar.setVisible(False)
            
            if failed_files:
                error_msg = f"Drag & Drop işlemi tamamlandı:\n\n" +\
                           f"Başarılı: {processed_count} dosya\n" +\
                           f"Başarısız: {len(failed_files)} dosya\n\n" +\
                           "Başarısız dosyalar:\n" + "\n".join(failed_files[:10])
                if len(failed_files) > 10:
                    error_msg += f"\n... ve {len(failed_files)-10} dosya daha"
                    
                QMessageBox.warning(self, "Belge Ekleme Sonucu", error_msg)
            else:
                QMessageBox.information(
                    self, "Başarılı", 
                    f"Tüm dosyalar başarıyla eklendi! (Drag & Drop)\n\nToplam: {processed_count} dosya"
                )
            
            # UI'yı güncelle
            self.document_tree.refresh_tree()
            self.stats_widget.refresh_stats()
            self.status_bar.showMessage(f"Drag & Drop tamamlandı: {processed_count} başarılı", 5000)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.logger.error(f"Drag & Drop işleme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Dosya işleme sırasında hata oluştu:\n{e}")
    
    def closeEvent(self, event):
        """Pencere kapatılırken"""
        try:
            # Ayarları kaydet
            if self.config.get('preferences.save_window_position', True):
                self._save_window_position()
            
            # Arama geçmişini kaydet
            if hasattr(self, 'search_widget'):
                search_history = self.search_widget.get_search_history()
                self.config.set('search.history', search_history)
            
            # Son arama sonuçlarını kaydet
            if hasattr(self, 'last_search_results') and self.last_search_results:
                self.config.set('search.last_results_count', len(self.last_search_results))
            
            # Konfigürasyonu kaydet
            self.config.save_config()
            
            # Temizlik
            if hasattr(self, 'file_watcher') and self.file_watcher:
                self.file_watcher.stop_watching()
            
            # Veritabanı bağlantısını kapat
            if hasattr(self, 'db') and self.db:
                self.db.close_connection()
            
            self.logger.info("Ana pencere kapatıldı")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Kapatma hatası: {e}")
            event.accept()
    
    def _save_window_position(self):
        """Pencere pozisyonunu kaydet"""
        try:
            # Pencere pozisyonu ve boyutu
            pos = self.pos()
            size = self.size()
            
            self.config.set('window.position.x', pos.x())
            self.config.set('window.position.y', pos.y())
            self.config.set('window.size.width', size.width())
            self.config.set('window.size.height', size.height())
            
            # Pencere durumu (maximized, minimized)
            if self.isMaximized():
                self.config.set('window.state', 'maximized')
            elif self.isMinimized():
                self.config.set('window.state', 'minimized')
            else:
                self.config.set('window.state', 'normal')
            
            self.logger.debug(f"Pencere pozisyonu kaydedildi: {pos.x()}, {pos.y()}, {size.width()}x{size.height()}")
            
        except Exception as e:
            self.logger.error(f"Pencere pozisyonu kaydetme hatası: {e}")
