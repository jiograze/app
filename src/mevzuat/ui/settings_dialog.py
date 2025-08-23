"""
Ayarlar dialog'u - sistem yapılandırması
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class FolderSettingsWidget(QWidget):
    """Klasör ayarları widget'ı"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)

        # Ana klasör
        main_group = QGroupBox("Ana Klasör")
        main_layout = QFormLayout(main_group)

        self.base_folder_edit = QLineEdit()
        self.base_folder_edit.setText(self.config.get("base_folder", ""))
        self.base_folder_edit.setReadOnly(True)

        base_folder_layout = QHBoxLayout()
        base_folder_layout.addWidget(self.base_folder_edit)

        browse_btn = QPushButton("Gözat...")
        browse_btn.clicked.connect(self.browse_base_folder)
        base_folder_layout.addWidget(browse_btn)

        main_layout.addRow("Ana Klasör:", base_folder_layout)

        # Alt klasörler
        self.raw_folder_edit = QLineEdit()
        self.raw_folder_edit.setText(self.config.get("raw_folder", "raw"))
        main_layout.addRow("Ham Belgeler:", self.raw_folder_edit)

        self.processed_folder_edit = QLineEdit()
        self.processed_folder_edit.setText(
            self.config.get("processed_folder", "processed")
        )
        main_layout.addRow("İşlenmiş Belgeler:", self.processed_folder_edit)

        self.quarantine_folder_edit = QLineEdit()
        self.quarantine_folder_edit.setText(
            self.config.get("quarantine_folder", "quarantine")
        )
        main_layout.addRow("Karantina:", self.quarantine_folder_edit)

        layout.addWidget(main_group)

        # Portable mod
        portable_group = QGroupBox("Portable Mod")
        portable_layout = QVBoxLayout(portable_group)

        self.portable_mode_cb = QCheckBox("Portable mod etkin")
        self.portable_mode_cb.setChecked(self.config.get("portable_mode", False))
        self.portable_mode_cb.toggled.connect(self.on_portable_mode_changed)
        portable_layout.addWidget(self.portable_mode_cb)

        portable_info = QLabel(
            "Portable modda tüm veriler uygulama klasöründe saklanır.\n"
            "Bu mod USB bellek gibi taşınabilir medya için uygundur."
        )
        portable_info.setStyleSheet("color: #666; font-size: 11px;")
        portable_info.setWordWrap(True)
        portable_layout.addWidget(portable_info)

        layout.addWidget(portable_group)

        layout.addStretch()

    def browse_base_folder(self):
        """Ana klasör seç"""
        folder = QFileDialog.getExistingDirectory(
            self, "Ana Klasör Seçin", self.base_folder_edit.text()
        )

        if folder:
            self.base_folder_edit.setText(folder)

    def on_portable_mode_changed(self, enabled):
        """Portable mod değiştiğinde"""
        if enabled:
            # Ana klasörü uygulama dizinine ayarla
            app_dir = Path(__file__).parent.parent.parent
            self.base_folder_edit.setText(str(app_dir))

    def get_values(self) -> Dict[str, Any]:
        """Değerleri al"""
        return {
            "base_folder": self.base_folder_edit.text(),
            "raw_folder": self.raw_folder_edit.text(),
            "processed_folder": self.processed_folder_edit.text(),
            "quarantine_folder": self.quarantine_folder_edit.text(),
            "portable_mode": self.portable_mode_cb.isChecked(),
        }


class SearchSettingsWidget(QWidget):
    """Arama ayarları widget'ı"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)

        # Genel arama ayarları
        general_group = QGroupBox("Genel Ayarlar")
        general_layout = QFormLayout(general_group)

        # Varsayılan arama türü
        self.default_search_type = QComboBox()
        self.default_search_type.addItems(["Karma", "Anahtar Kelime", "Semantik"])
        current_type = self.config.get("search.default_type", "mixed")
        if current_type == "keyword":
            self.default_search_type.setCurrentText("Anahtar Kelime")
        elif current_type == "semantic":
            self.default_search_type.setCurrentText("Semantik")
        else:
            self.default_search_type.setCurrentText("Karma")

        general_layout.addRow("Varsayılan Arama Türü:", self.default_search_type)

        # Maksimum sonuç sayısı
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setMinimum(10)
        self.max_results_spin.setMaximum(1000)
        self.max_results_spin.setValue(self.config.get("search.max_results", 100))
        general_layout.addRow("Maksimum Sonuç:", self.max_results_spin)

        # Benzerlik eşiği
        similarity_layout = QHBoxLayout()

        self.similarity_slider = QSlider(Qt.Horizontal)
        self.similarity_slider.setMinimum(1)
        self.similarity_slider.setMaximum(10)
        threshold = int(self.config.get("search.similarity_threshold", 0.6) * 10)
        self.similarity_slider.setValue(threshold)
        self.similarity_slider.valueChanged.connect(self.update_similarity_label)

        self.similarity_label = QLabel(f"{threshold/10:.1f}")

        similarity_layout.addWidget(self.similarity_slider)
        similarity_layout.addWidget(self.similarity_label)

        general_layout.addRow("Benzerlik Eşiği:", similarity_layout)

        # Cache boyutu
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setMinimum(10)
        self.cache_size_spin.setMaximum(1000)
        self.cache_size_spin.setValue(self.config.get("search.cache_size", 100))
        self.cache_size_spin.setSuffix(" sonuç")
        general_layout.addRow("Cache Boyutu:", self.cache_size_spin)

        layout.addWidget(general_group)

        # Semantik arama ayarları
        semantic_group = QGroupBox("Semantik Arama")
        semantic_layout = QFormLayout(semantic_group)

        # Model adı
        self.model_name_combo = QComboBox()
        self.model_name_combo.setEditable(True)
        models = [
            "sentence-transformers/distiluse-base-multilingual-cased",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "sentence-transformers/all-MiniLM-L6-v2",
            "dbmdz/bert-base-turkish-cased",
        ]
        self.model_name_combo.addItems(models)
        current_model = self.config.get("search.semantic_model", models[0])
        self.model_name_combo.setCurrentText(current_model)
        semantic_layout.addRow("Model:", self.model_name_combo)

        # Batch boyutu
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(100)
        self.batch_size_spin.setValue(self.config.get("search.batch_size", 32))
        semantic_layout.addRow("Batch Boyutu:", self.batch_size_spin)

        # Index rebuild threshold
        self.rebuild_threshold_spin = QSpinBox()
        self.rebuild_threshold_spin.setMinimum(10)
        self.rebuild_threshold_spin.setMaximum(10000)
        self.rebuild_threshold_spin.setValue(
            self.config.get("search.rebuild_threshold", 1000)
        )
        semantic_layout.addRow("Yeniden İndeks Eşiği:", self.rebuild_threshold_spin)

        layout.addWidget(semantic_group)

        # Filtreleme ayarları
        filter_group = QGroupBox("Filtreleme")
        filter_layout = QVBoxLayout(filter_group)

        self.include_repealed_cb = QCheckBox(
            "Varsayılan olarak mülga maddeleri dahil et"
        )
        self.include_repealed_cb.setChecked(
            self.config.get("search.include_repealed", False)
        )
        filter_layout.addWidget(self.include_repealed_cb)

        self.include_amended_cb = QCheckBox(
            "Varsayılan olarak değişiklik olanları dahil et"
        )
        self.include_amended_cb.setChecked(
            self.config.get("search.include_amended", True)
        )
        filter_layout.addWidget(self.include_amended_cb)

        layout.addWidget(filter_group)

        layout.addStretch()

    def update_similarity_label(self, value):
        """Benzerlik eşiği etiketini güncelle"""
        self.similarity_label.setText(f"{value/10:.1f}")

    def update_similarity_label(self, value):
        """Benzerlik etiketini güncelle"""
        self.similarity_label.setText(f"{value/10:.1f}")

    def get_values(self) -> Dict[str, Any]:
        """Değerleri al"""
        search_type = self.default_search_type.currentText().lower()
        if search_type == "anahtar kelime":
            search_type = "keyword"
        elif search_type == "semantik":
            search_type = "semantic"
        else:
            search_type = "mixed"

        return {
            "search.default_type": search_type,
            "search.max_results": self.max_results_spin.value(),
            "search.similarity_threshold": self.similarity_slider.value() / 10.0,
            "search.cache_size": self.cache_size_spin.value(),
            "search.semantic_model": self.model_name_combo.currentText(),
            "search.batch_size": self.batch_size_spin.value(),
            "search.rebuild_threshold": self.rebuild_threshold_spin.value(),
            "search.include_repealed": self.include_repealed_cb.isChecked(),
            "search.include_amended": self.include_amended_cb.isChecked(),
        }


class ProcessingSettingsWidget(QWidget):
    """İşleme ayarları widget'ı"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)

        # File watcher ayarları
        watcher_group = QGroupBox("Dosya İzleme")
        watcher_layout = QFormLayout(watcher_group)

        # İzleme etkin
        self.watch_enabled_cb = QCheckBox("Dosya izleme etkin")
        self.watch_enabled_cb.setChecked(self.config.get("file_watcher.enabled", True))
        watcher_layout.addRow(self.watch_enabled_cb)

        # Tarama aralığı
        self.scan_interval_spin = QSpinBox()
        self.scan_interval_spin.setMinimum(1)
        self.scan_interval_spin.setMaximum(3600)
        self.scan_interval_spin.setValue(
            self.config.get("file_watcher.scan_interval", 10)
        )
        self.scan_interval_spin.setSuffix(" saniye")
        watcher_layout.addRow("Tarama Aralığı:", self.scan_interval_spin)

        # Stabilite kontrolü
        self.stability_time_spin = QSpinBox()
        self.stability_time_spin.setMinimum(1)
        self.stability_time_spin.setMaximum(300)
        self.stability_time_spin.setValue(
            self.config.get("file_watcher.stability_time", 5)
        )
        self.stability_time_spin.setSuffix(" saniye")
        watcher_layout.addRow("Stabilite Süresi:", self.stability_time_spin)

        layout.addWidget(watcher_group)

        # Belge işleme ayarları
        processing_group = QGroupBox("Belge İşleme")
        processing_layout = QFormLayout(processing_group)

        # Paralel işlem sayısı
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setMinimum(1)
        self.max_workers_spin.setMaximum(16)
        self.max_workers_spin.setValue(self.config.get("processing.max_workers", 4))
        processing_layout.addRow("Paralel İşlem Sayısı:", self.max_workers_spin)

        # OCR etkin
        self.ocr_enabled_cb = QCheckBox("OCR etkin (scanned PDF için)")
        self.ocr_enabled_cb.setChecked(self.config.get("processing.ocr_enabled", True))
        processing_layout.addRow(self.ocr_enabled_cb)

        # Maksimum dosya boyutu (MB)
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setMinimum(1)
        self.max_file_size_spin.setMaximum(1000)
        self.max_file_size_spin.setValue(
            self.config.get("processing.max_file_size_mb", 50)
        )
        self.max_file_size_spin.setSuffix(" MB")
        processing_layout.addRow("Maksimum Dosya Boyutu:", self.max_file_size_spin)

        layout.addWidget(processing_group)

        # Metin işleme
        text_group = QGroupBox("Metin İşleme")
        text_layout = QFormLayout(text_group)

        # Minimum madde uzunluğu
        self.min_article_length_spin = QSpinBox()
        self.min_article_length_spin.setMinimum(10)
        self.min_article_length_spin.setMaximum(1000)
        self.min_article_length_spin.setValue(
            self.config.get("text_processing.min_article_length", 50)
        )
        self.min_article_length_spin.setSuffix(" karakter")
        text_layout.addRow("Minimum Madde Uzunluğu:", self.min_article_length_spin)

        # Maksimum madde uzunluğu
        self.max_article_length_spin = QSpinBox()
        self.max_article_length_spin.setMinimum(100)
        self.max_article_length_spin.setMaximum(50000)
        self.max_article_length_spin.setValue(
            self.config.get("text_processing.max_article_length", 10000)
        )
        self.max_article_length_spin.setSuffix(" karakter")
        text_layout.addRow("Maksimum Madde Uzunluğu:", self.max_article_length_spin)

        layout.addWidget(text_group)

        layout.addStretch()

    def get_values(self) -> Dict[str, Any]:
        """Değerleri al"""
        return {
            "file_watcher.enabled": self.watch_enabled_cb.isChecked(),
            "file_watcher.scan_interval": self.scan_interval_spin.value(),
            "file_watcher.stability_time": self.stability_time_spin.value(),
            "processing.max_workers": self.max_workers_spin.value(),
            "processing.ocr_enabled": self.ocr_enabled_cb.isChecked(),
            "processing.max_file_size_mb": self.max_file_size_spin.value(),
            "text_processing.min_article_length": self.min_article_length_spin.value(),
            "text_processing.max_article_length": self.max_article_length_spin.value(),
        }

    def get_values(self) -> Dict[str, Any]:
        """Değerleri al"""
        return {
            "file_watcher.enabled": self.watch_enabled_cb.isChecked(),
            "file_watcher.scan_interval": self.scan_interval_spin.value(),
            "file_watcher.stability_time": self.stability_time_spin.value(),
            "processing.max_workers": self.max_workers_spin.value(),
            "processing.ocr_enabled": self.ocr_enabled_cb.isChecked(),
            "processing.max_file_size_mb": self.max_file_size_spin.value(),
            "text_processing.min_article_length": self.min_article_length_spin.value(),
            "text_processing.max_article_length": self.max_article_length_spin.value(),
        }


class UISettingsWidget(QWidget):
    """UI ayarları widget'ı"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)

        # Görünüm ayarları
        appearance_group = QGroupBox("Görünüm")
        appearance_layout = QFormLayout(appearance_group)

        # Tema
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Sistem", "Açık", "Koyu"])
        current_theme = self.config.get("preferences.theme", "system")
        if current_theme == "light":
            self.theme_combo.setCurrentText("Açık")
        elif current_theme == "dark":
            self.theme_combo.setCurrentText("Koyu")
        else:
            self.theme_combo.setCurrentText("Sistem")

        appearance_layout.addRow("Tema:", self.theme_combo)

        # Font boyutu
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["Küçük", "Orta", "Büyük"])
        current_font = self.config.get("preferences.font_size", "medium")
        if current_font == "small":
            self.font_size_combo.setCurrentText("Küçük")
        elif current_font == "large":
            self.font_size_combo.setCurrentText("Büyük")
        else:
            self.font_size_combo.setCurrentText("Orta")

        appearance_layout.addRow("Font Boyutu:", self.font_size_combo)

        layout.addWidget(appearance_group)

        # Pencere ayarları
        window_group = QGroupBox("Pencere")
        window_layout = QVBoxLayout(window_group)

        self.save_window_position_cb = QCheckBox("Pencere pozisyonunu kaydet")
        self.save_window_position_cb.setChecked(
            self.config.get("preferences.save_window_position", True)
        )
        window_layout.addWidget(self.save_window_position_cb)

        self.minimize_to_tray_cb = QCheckBox("Sistem tepsisine küçült")
        self.minimize_to_tray_cb.setChecked(
            self.config.get("preferences.minimize_to_tray", False)
        )
        window_layout.addWidget(self.minimize_to_tray_cb)

        self.start_minimized_cb = QCheckBox("Küçük olarak başlat")
        self.start_minimized_cb.setChecked(
            self.config.get("preferences.start_minimized", False)
        )
        window_layout.addWidget(self.start_minimized_cb)

        layout.addWidget(window_group)

        # Sonuç görüntüleme
        results_group = QGroupBox("Sonuç Görüntüleme")
        results_layout = QFormLayout(results_group)

        # Varsayılan görünüm
        self.default_view_combo = QComboBox()
        self.default_view_combo.addItems(["Tablo", "Liste"])
        current_view = self.config.get("preferences.default_result_view", "table")
        if current_view == "list":
            self.default_view_combo.setCurrentText("Liste")
        else:
            self.default_view_combo.setCurrentText("Tablo")

        results_layout.addRow("Varsayılan Görünüm:", self.default_view_combo)

        # Highlight rengi
        self.highlight_color_combo = QComboBox()
        self.highlight_color_combo.addItems(["Sarı", "Mavi", "Yeşil", "Kırmızı"])
        current_color = self.config.get("preferences.highlight_color", "yellow")
        if current_color == "blue":
            self.highlight_color_combo.setCurrentText("Mavi")
        elif current_color == "green":
            self.highlight_color_combo.setCurrentText("Yeşil")
        elif current_color == "red":
            self.highlight_color_combo.setCurrentText("Kırmızı")
        else:
            self.highlight_color_combo.setCurrentText("Sarı")

        results_layout.addRow("Vurgulama Rengi:", self.highlight_color_combo)

        # Sayfa başına sonuç
        self.results_per_page_spin = QSpinBox()
        self.results_per_page_spin.setMinimum(10)
        self.results_per_page_spin.setMaximum(500)
        self.results_per_page_spin.setValue(
            self.config.get("preferences.results_per_page", 50)
        )
        results_layout.addRow("Sayfa Başına Sonuç:", self.results_per_page_spin)

        layout.addWidget(results_group)

        layout.addStretch()

    def get_values(self) -> Dict[str, Any]:
        """Değerleri al"""
        # Tema
        theme = self.theme_combo.currentText().lower()
        if theme == "açık":
            theme = "light"
        elif theme == "koyu":
            theme = "dark"
        else:
            theme = "system"

        # Font boyutu
        font_size = self.font_size_combo.currentText().lower()
        if font_size == "küçük":
            font_size = "small"
        elif font_size == "büyük":
            font_size = "large"
        else:
            font_size = "medium"

        # Görünüm
        view = "table" if self.default_view_combo.currentText() == "Tablo" else "list"

        # Highlight rengi
        color_map = {
            "Sarı": "yellow",
            "Mavi": "blue",
            "Yeşil": "green",
            "Kırmızı": "red",
        }
        highlight_color = color_map.get(
            self.highlight_color_combo.currentText(), "yellow"
        )

        return {
            "preferences.theme": theme,
            "preferences.font_size": font_size,
            "preferences.save_window_position": self.save_window_position_cb.isChecked(),
            "preferences.minimize_to_tray": self.minimize_to_tray_cb.isChecked(),
            "preferences.start_minimized": self.start_minimized_cb.isChecked(),
            "preferences.default_result_view": view,
            "preferences.highlight_color": highlight_color,
            "preferences.results_per_page": self.results_per_page_spin.value(),
        }


class AdvancedSettingsWidget(QWidget):
    """Gelişmiş ayarlar widget'ı"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)

        # Loglama
        logging_group = QGroupBox("Loglama")
        logging_layout = QFormLayout(logging_group)

        # Log seviyesi
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        current_level = self.config.get("logging.level", "INFO")
        self.log_level_combo.setCurrentText(current_level)
        logging_layout.addRow("Log Seviyesi:", self.log_level_combo)

        # Log dosya boyutu
        self.log_file_size_spin = QSpinBox()
        self.log_file_size_spin.setMinimum(1)
        self.log_file_size_spin.setMaximum(100)
        self.log_file_size_spin.setValue(
            self.config.get("logging.max_file_size_mb", 10)
        )
        self.log_file_size_spin.setSuffix(" MB")
        logging_layout.addRow("Maksimum Log Boyutu:", self.log_file_size_spin)

        # Backup sayısı
        self.log_backup_count_spin = QSpinBox()
        self.log_backup_count_spin.setMinimum(1)
        self.log_backup_count_spin.setMaximum(20)
        self.log_backup_count_spin.setValue(self.config.get("logging.backup_count", 5))
        logging_layout.addRow("Log Backup Sayısı:", self.log_backup_count_spin)

        layout.addWidget(logging_group)

        # Performans
        performance_group = QGroupBox("Performans")
        performance_layout = QFormLayout(performance_group)

        # Thread pool boyutu
        self.thread_pool_size_spin = QSpinBox()
        self.thread_pool_size_spin.setMinimum(1)
        self.thread_pool_size_spin.setMaximum(32)
        self.thread_pool_size_spin.setValue(
            self.config.get("performance.thread_pool_size", 8)
        )
        performance_layout.addRow("Thread Pool Boyutu:", self.thread_pool_size_spin)

        # Memory limit
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setMinimum(256)
        self.memory_limit_spin.setMaximum(8192)
        self.memory_limit_spin.setValue(
            self.config.get("performance.memory_limit_mb", 1024)
        )
        self.memory_limit_spin.setSuffix(" MB")
        performance_layout.addRow("Bellek Limiti:", self.memory_limit_spin)

        layout.addWidget(performance_group)

        # Güvenlik
        security_group = QGroupBox("Güvenlik")
        security_layout = QVBoxLayout(security_group)

        self.quarantine_unknown_cb = QCheckBox("Bilinmeyen dosyaları karantinaya al")
        self.quarantine_unknown_cb.setChecked(
            self.config.get("security.quarantine_unknown", True)
        )
        security_layout.addWidget(self.quarantine_unknown_cb)

        self.validate_documents_cb = QCheckBox("Belge bütünlüğünü doğrula")
        self.validate_documents_cb.setChecked(
            self.config.get("security.validate_documents", True)
        )
        security_layout.addWidget(self.validate_documents_cb)

        layout.addWidget(security_group)

        # Yedekleme
        backup_group = QGroupBox("Yedekleme")
        backup_layout = QFormLayout(backup_group)

        self.auto_backup_cb = QCheckBox("Otomatik yedekleme etkin")
        self.auto_backup_cb.setChecked(self.config.get("backup.auto_backup", False))
        backup_layout.addRow(self.auto_backup_cb)

        # Yedekleme aralığı
        self.backup_interval_combo = QComboBox()
        self.backup_interval_combo.addItems(["Günlük", "Haftalık", "Aylık"])
        current_interval = self.config.get("backup.interval", "weekly")
        if current_interval == "daily":
            self.backup_interval_combo.setCurrentText("Günlük")
        elif current_interval == "monthly":
            self.backup_interval_combo.setCurrentText("Aylık")
        else:
            self.backup_interval_combo.setCurrentText("Haftalık")

        backup_layout.addRow("Yedekleme Aralığı:", self.backup_interval_combo)

        # Yedek sayısı
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setMinimum(1)
        self.backup_count_spin.setMaximum(50)
        self.backup_count_spin.setValue(self.config.get("backup.keep_count", 10))
        backup_layout.addRow("Tutulacak Yedek Sayısı:", self.backup_count_spin)

        layout.addWidget(backup_group)

        # Test butonları
        test_group = QGroupBox("Test & Doğrulama")
        test_layout = QHBoxLayout(test_group)

        test_logging_btn = QPushButton("Loglama Test Et")
        test_logging_btn.clicked.connect(self.test_logging)
        test_layout.addWidget(test_logging_btn)

        test_performance_btn = QPushButton("Performans Test Et")
        test_performance_btn.clicked.connect(self.test_performance)
        test_layout.addWidget(test_performance_btn)

        test_security_btn = QPushButton("Güvenlik Test Et")
        test_security_btn.clicked.connect(self.test_security)
        test_layout.addWidget(test_security_btn)

        layout.addWidget(test_group)

        layout.addStretch()

    def apply_advanced_settings(self):
        """Gelişmiş ayarları uygula"""
        try:
            # Loglama ayarlarını uygula
            self._apply_logging_settings()

            # Performans ayarlarını uygula
            self._apply_performance_settings()

            # Güvenlik ayarlarını uygula
            self._apply_security_settings()

            # Yedekleme ayarlarını uygula
            self._apply_backup_settings()

            self.logger.info("Gelişmiş ayarlar uygulandı")

        except Exception as e:
            self.logger.error(f"Gelişmiş ayarlar uygulama hatası: {e}")
            raise

    def _apply_logging_settings(self):
        """Loglama ayarlarını uygula"""
        try:
            # Log seviyesini güncelle
            log_level = self.log_level_combo.currentText()
            self.config.set("logging.level", log_level)

            # Logger'ı yeniden yapılandır
            import logging

            logging.getLogger().setLevel(getattr(logging, log_level))

            # Log dosya boyutunu güncelle
            max_size = self.log_file_size_spin.value()
            self.config.set("logging.max_file_size_mb", max_size)

            # Backup sayısını güncelle
            backup_count = self.log_backup_count_spin.value()
            self.config.set("logging.backup_count", backup_count)

        except Exception as e:
            self.logger.error(f"Loglama ayarları uygulama hatası: {e}")

    def _apply_performance_settings(self):
        """Performans ayarlarını uygula"""
        try:
            # Thread pool boyutunu güncelle
            thread_pool_size = self.thread_pool_size_spin.value()
            self.config.set("performance.thread_pool_size", thread_pool_size)

            # Bellek limitini güncelle
            memory_limit = self.memory_limit_spin.value()
            self.config.set("performance.memory_limit_mb", memory_limit)

        except Exception as e:
            self.logger.error(f"Performans ayarları uygulama hatası: {e}")

    def _apply_security_settings(self):
        """Güvenlik ayarlarını uygula"""
        try:
            # Karantina ayarını güncelle
            quarantine = self.quarantine_unknown_cb.isChecked()
            self.config.set("security.quarantine_unknown", quarantine)

            # Belge doğrulama ayarını güncelle
            validate = self.validate_documents_cb.isChecked()
            self.config.set("security.validate_documents", validate)

        except Exception as e:
            self.logger.error(f"Güvenlik ayarları uygulama hatası: {e}")

    def _apply_backup_settings(self):
        """Yedekleme ayarlarını uygula"""
        try:
            # Otomatik yedekleme ayarını güncelle
            auto_backup = self.auto_backup_cb.isChecked()
            self.config.set("backup.auto_backup", auto_backup)

            # Yedekleme aralığını güncelle
            interval_text = self.backup_interval_combo.currentText()
            interval_map = {"Günlük": "daily", "Haftalık": "weekly", "Aylık": "monthly"}
            interval = interval_map.get(interval_text, "weekly")
            self.config.set("backup.interval", interval)

            # Yedek sayısını güncelle
            backup_count = self.backup_count_spin.value()
            self.config.set("backup.keep_count", backup_count)

        except Exception as e:
            self.logger.error(f"Yedekleme ayarları uygulama hatası: {e}")

    def test_logging(self):
        """Loglama ayarlarını test et"""
        try:
            self.logger.debug("Bu bir DEBUG mesajıdır")
            self.logger.info("Bu bir INFO mesajıdır")
            self.logger.warning("Bu bir WARNING mesajıdır")
            self.logger.error("Bu bir ERROR mesajıdır")

            QMessageBox.information(self, "Test", "Loglama test mesajları gönderildi")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Loglama test hatası:\n{e}")

    def test_performance(self):
        """Performans ayarlarını test et"""
        try:
            import time

            start_time = time.time()

            # Basit performans testi
            for i in range(1000000):
                pass

            elapsed_time = time.time() - start_time

            QMessageBox.information(
                self,
                "Test",
                f"Performans testi tamamlandı\nSüre: {elapsed_time:.3f} saniye",
            )

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Performans test hatası:\n{e}")

    def test_security(self):
        """Güvenlik ayarlarını test et"""
        try:
            # Güvenlik testi
            security_status = {
                "Karantina": self.quarantine_unknown_cb.isChecked(),
                "Belge Doğrulama": self.validate_documents_cb.isChecked(),
                "Log Seviyesi": self.log_level_combo.currentText(),
            }

            status_text = "\n".join([f"{k}: {v}" for k, v in security_status.items()])

            QMessageBox.information(
                self, "Güvenlik Testi", f"Güvenlik ayarları:\n{status_text}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Güvenlik test hatası:\n{e}")

    def get_values(self) -> Dict[str, Any]:
        """Değerleri al"""
        # Backup interval
        interval = self.backup_interval_combo.currentText().lower()
        if interval == "günlük":
            interval = "daily"
        elif interval == "aylık":
            interval = "monthly"
        else:
            interval = "weekly"

        return {
            "logging.level": self.log_level_combo.currentText(),
            "logging.max_file_size_mb": self.log_file_size_spin.value(),
            "logging.backup_count": self.log_backup_count_spin.value(),
            "performance.thread_pool_size": self.thread_pool_size_spin.value(),
            "performance.memory_limit_mb": self.memory_limit_spin.value(),
            "security.quarantine_unknown": self.quarantine_unknown_cb.isChecked(),
            "security.validate_documents": self.validate_documents_cb.isChecked(),
            "backup.auto_backup": self.auto_backup_cb.isChecked(),
            "backup.interval": interval,
            "backup.keep_count": self.backup_count_spin.value(),
        }


class SettingsDialog(QDialog):
    """Ana ayarlar dialog'u"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        self.setWindowTitle("Ayarlar")
        self.setModal(True)
        self.resize(600, 500)

        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)

        # Tab widget
        self.tab_widget = QTabWidget()

        # Klasör ayarları
        self.folder_settings = FolderSettingsWidget(self.config)
        self.tab_widget.addTab(self.folder_settings, "📁 Klasörler")

        # Arama ayarları
        self.search_settings = SearchSettingsWidget(self.config)
        self.tab_widget.addTab(self.search_settings, "🔍 Arama")

        # İşleme ayarları
        self.processing_settings = ProcessingSettingsWidget(self.config)
        self.tab_widget.addTab(self.processing_settings, "⚙️ İşleme")

        # UI ayarları
        self.ui_settings = UISettingsWidget(self.config)
        self.tab_widget.addTab(self.ui_settings, "🎨 Arayüz")

        # Gelişmiş ayarlar
        self.advanced_settings = AdvancedSettingsWidget(self.config)
        self.tab_widget.addTab(self.advanced_settings, "🔧 Gelişmiş")

        layout.addWidget(self.tab_widget)

        # Butonlar
        button_layout = QHBoxLayout()

        # Varsayılanlara dön
        defaults_btn = QPushButton("Varsayılanlara Dön")
        defaults_btn.clicked.connect(self.restore_defaults)
        button_layout.addWidget(defaults_btn)

        button_layout.addStretch()

        # İptal / Tamam
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Tamam")
        ok_btn.clicked.connect(self.accept_settings)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def load_current_settings(self):
        """Mevcut ayarları yükle"""
        # Widget'lar kendi ayarlarını yükler
        pass

    def accept_settings(self):
        """Ayarları kabul et"""
        try:
            # Tüm widget'lardan değerleri al
            all_values = {}

            all_values.update(self.folder_settings.get_values())
            all_values.update(self.search_settings.get_values())
            all_values.update(self.processing_settings.get_values())
            all_values.update(self.ui_settings.get_values())
            all_values.update(self.advanced_settings.get_values())

            # Ayarları kaydet
            for key, value in all_values.items():
                self.config.set(key, value)

            # Dosyaya yaz
            self.config.save()

            self.logger.info("Ayarlar kaydedildi")
            self.accept()

        except Exception as e:
            self.logger.error(f"Ayar kaydetme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Ayarlar kaydedilemedi:\n{e}")

    def restore_defaults(self):
        """Varsayılan ayarları geri yükle"""
        reply = QMessageBox.question(
            self,
            "Varsayılanlara Dön",
            "Tüm ayarlar varsayılan değerlere döndürülecek. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                # Config'i sıfırla
                self.config.reset_to_defaults()

                # Dialog'u yeniden oluştur
                self.close()
                new_dialog = SettingsDialog(self.config, self.parent())
                new_dialog.exec_()

            except Exception as e:
                QMessageBox.critical(
                    self, "Hata", f"Varsayılan ayarlar yüklenemedi:\n{e}"
                )
