"""
Ana uygulama yöneticisi - tüm bileşenleri koordine eder
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread

from ..utils.config_manager import ConfigManager
from ..utils.logger import setup_logger
from ..core.database_manager import DatabaseManager
from ..core.file_watcher import FileWatcher
from ..core.document_processor import DocumentProcessor
from ..core.search_engine import SearchEngine
from ..ui.main_window import MainWindow

class MevzuatApp:
    """Ana uygulama sınıfı - tüm bileşenleri yönetir"""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.config: Optional[ConfigManager] = None
        self.db: Optional[DatabaseManager] = None
        self.file_watcher: Optional[FileWatcher] = None
        self.document_processor: Optional[DocumentProcessor] = None
        self.search_engine: Optional[SearchEngine] = None
        self.main_window: Optional[MainWindow] = None
        self.qt_app: Optional[QApplication] = None
        
        self._initialize()
    
    def _initialize(self):
        """Tüm bileşenleri başlat"""
        try:
            self.logger.info("Mevzuat sistemi başlatılıyor...")
            
            # Konfigürasyonu yükle
            self.config = ConfigManager()
            
            # İlk çalışma kontrolü
            if self.config.get('exe.first_run_check', True):
                self._handle_first_run()
            
            # Veritabanını başlat
            self.db = DatabaseManager(self.config)
            self.db.initialize()
            
            # Belge işleyiciyi başlat
            self.document_processor = DocumentProcessor(self.config, self.db)
            
            # Arama motorunu başlat
            self.search_engine = SearchEngine(self.config, self.db)
            
            # Dosya izleyiciyi başlat (eğer etkinse)
            if self.config.get('watch_enabled', True):
                self.file_watcher = FileWatcher(
                    self.config, 
                    self.document_processor
                )
            
            self.logger.info("Tüm bileşenler başarıyla başlatıldı")
            
        except Exception as e:
            self.logger.error(f"Başlatma hatası: {e}")
            raise
    
    def _handle_first_run(self):
        """İlk çalışma kurulum sihirbazı"""
        self.logger.info("İlk çalışma kurulumu başlatılıyor...")
        
        # Temel klasör yapısını oluştur
        base_folder = self.config.get('base_folder')
        if base_folder and not os.path.exists(base_folder):
            self._create_directory_structure(base_folder)
        
        # İlk çalışma flag'ini kapat
        self.config.set('exe.first_run_check', False)
        self.config.save()
    
    def _create_directory_structure(self, base_folder: str):
        """Temel klasör yapısını oluştur"""
        directories = [
            'config',
            'raw',
            'mevzuat/Anayasa',
            'mevzuat/Kanun',
            'mevzuat/KHK',
            'mevzuat/Tüzük',
            'mevzuat/Yönetmelik',
            'mevzuat/Yönerge_Genelge',
            'mevzuat/Diger',
            'mevzuat/_Özel_Kategoriler',
            'db',
            'index',
            'logs',
            'temp/ocr',
            'temp/export',
            'quarantine',
            'backup',
            'models',
            'templates'
        ]
        
        for directory in directories:
            dir_path = os.path.join(base_folder, directory)
            os.makedirs(dir_path, exist_ok=True)
            self.logger.info(f"Klasör oluşturuldu: {dir_path}")
    
    def run(self):
        """Ana uygulamayı çalıştır"""
        try:
            # Qt uygulamasını başlat
            self.qt_app = QApplication(sys.argv)
            
            # Ana pencereyi oluştur ve göster
            self.main_window = MainWindow(
                config=self.config,
                db=self.db,
                search_engine=self.search_engine,
                document_processor=self.document_processor,
                file_watcher=self.file_watcher
            )
            
            self.main_window.show()
            
            # Dosya izleyiciyi başlat (eğer varsa)
            if self.file_watcher:
                self.file_watcher.start_watching()
            
            self.logger.info("GUI başlatıldı, uygulama hazır")
            
            # Olay döngüsünü başlat
            sys.exit(self.qt_app.exec_())
            
        except Exception as e:
            self.logger.error(f"Uygulama çalışma hatası: {e}")
            raise
    
    def shutdown(self):
        """Uygulamayı temiz şekilde kapat"""
        try:
            self.logger.info("Uygulama kapatılıyor...")
            
            # Dosya izleyiciyi durdur
            if self.file_watcher:
                self.file_watcher.stop_watching()
            
            # Veritabanı bağlantısını kapat
            if self.db:
                self.db.close()
            
            # Konfigürasyonu kaydet
            if self.config:
                self.config.save()
            
            self.logger.info("Uygulama temiz şekilde kapatıldı")
            
        except Exception as e:
            self.logger.error(f"Kapatma hatası: {e}")
    
    def __del__(self):
        """Nesne yok edilirken temizlik yap"""
        try:
            self.shutdown()
        except:
            pass
