"""
Sonuç görüntüleme widget'ı - arama sonuçlarını gösterir
"""

import logging
from typing import List, Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QTextEdit, QLabel,
    QPushButton, QHeaderView, QAbstractItemView, QMenu,
    QFrame, QSplitter, QTabWidget, QListWidget, QListWidgetItem,
    QGroupBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QSize, QTimer
)
from PyQt5.QtGui import (
    QFont, QColor, QBrush, QIcon, QPixmap, QPainter
)

from ..core.search_engine import SearchResult

class ResultItem(QListWidgetItem):
    """Sonuç listesi item'ı"""
    
    def __init__(self, result: SearchResult):
        super().__init__()
        self.result = result
        
        # Görünümü ayarla
        self.update_display()
    
    def update_display(self):
        """Görünümü güncelle"""
        # Ana başlık
        title = self.result.title or f"{self.result.document_type} - Madde {self.result.article_number}"
        
        # Alt başlık bilgileri
        subtitle_parts = []
        if self.result.document_title:
            subtitle_parts.append(self.result.document_title)
        if self.result.law_number:
            subtitle_parts.append(f"Kanun No: {self.result.law_number}")
        
        subtitle = " | ".join(subtitle_parts)
        
        # Durum göstergeleri
        status_indicators = []
        if self.result.is_repealed:
            status_indicators.append("🚫 MÜLGA")
        elif self.result.is_amended:
            status_indicators.append("📝 DEĞİŞİK")
        
        # Skor gösterimi
        score_text = f"Skor: {self.result.score:.3f}"
        match_type_icon = "🎯" if self.result.match_type == "exact" else "🔍"
        
        # HTML formatında metin oluştur
        display_text = f"""
        <div style="padding: 8px;">
            <div style="font-weight: bold; font-size: 14px; margin-bottom: 4px;">
                {match_type_icon} {title}
            </div>
            <div style="color: #666; font-size: 12px; margin-bottom: 4px;">
                {subtitle}
            </div>
            <div style="color: #333; font-size: 13px; margin-bottom: 6px;">
                {self.result.content[:200]}...
            </div>
            <div style="font-size: 11px; color: #888;">
                <span>{score_text}</span>
                {' | '.join(status_indicators) if status_indicators else ''}
            </div>
        </div>
        """
        
        self.setText(display_text)
        self.setData(Qt.UserRole, self.result)

class ResultTableWidget(QTableWidget):
    """Sonuç tablosu widget'ı"""
    
    result_selected = pyqtSignal(SearchResult)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results: List[SearchResult] = []
        
        self.init_ui()
    
    def init_ui(self):
        """UI'yi oluştur"""
        # Sütun başlıkları
        headers = ["Tür", "Başlık", "Belge", "Madde", "Skor", "Durum"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Ayarlar
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        
        # Sütun genişlikleri
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Tür
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Başlık
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Belge
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Madde
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Skor
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Durum
        
        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Seçim değişimi
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def display_results(self, results: List[SearchResult]):
        """Sonuçları göster"""
        try:
            self.clear()
            self.results = results
            
            if not results:
                return
            
            # Satır sayısını ayarla
            self.setRowCount(len(results))
            
            for row, result in enumerate(results):
                # Tür
                type_item = QTableWidgetItem(result.document_type or "Bilinmeyen")
                self.setItem(row, 0, type_item)
                
                # Başlık
                title = result.title or f'Madde {result.article_number}' or 'Başlıksız'
                title_item = QTableWidgetItem(title)
                self.setItem(row, 1, title_item)
                
                # Belge
                doc_title = result.document_title or 'Bilinmeyen'
                doc_item = QTableWidgetItem(doc_title)
                self.setItem(row, 2, doc_item)
                
                # Madde
                article_item = QTableWidgetItem(str(result.article_number or ''))
                self.setItem(row, 3, article_item)
                
                # Skor
                score_item = QTableWidgetItem(f"{result.score:.3f}")
                self.setItem(row, 4, score_item)
                
                # Durum
                status = "Aktif"
                if result.is_repealed:
                    status = "Mülga"
                elif result.is_amended:
                    status = "Değişik"
                status_item = QTableWidgetItem(status)
                self.setItem(row, 5, status_item)
                
                # Renk kodlaması
                if result.is_repealed:
                    for col in range(6):
                        item = self.item(row, col)
                        if item:
                            item.setForeground(QBrush(QColor(150, 150, 150)))
                elif result.is_amended:
                    for col in range(6):
                        item = self.item(row, col)
                        if item:
                            item.setForeground(QBrush(QColor(200, 100, 0)))
                
                # User data
                for col in range(6):
                    item = self.item(row, col)
                    if item:
                        item.setData(Qt.UserRole, result)
            
            self.logger.info(f"{len(results)} sonuç tabloda gösterildi")
            
        except Exception as e:
            self.logger.error(f"Tablo sonuç gösterme hatası: {e}")
    
    def show_context_menu(self, position):
        """Context menu göster"""
        try:
            current_row = self.currentRow()
            if current_row < 0:
                return
            
            result = self.results[current_row]
            if not result:
                return
            
            menu = QMenu(self)
            
            # Detay göster
            show_action = menu.addAction("Detayları Göster")
            show_action.triggered.connect(lambda: self.result_selected.emit(result))
            
            # Panoya kopyala
            copy_action = menu.addAction("Panoya Kopyala")
            copy_action.triggered.connect(lambda: self.copy_to_clipboard(result))
            
            # Favorilere ekle
            fav_action = menu.addAction("Favorilere Ekle")
            fav_action.triggered.connect(lambda: self.add_to_favorites(result))
            
            # Not ekle
            note_action = menu.addAction("Not Ekle")
            note_action.triggered.connect(lambda: self.add_note(result))
            
            menu.exec_(self.mapToGlobal(position))
            
        except Exception as e:
            self.logger.error(f"Context menu hatası: {e}")
    
    def copy_to_clipboard(self, result: SearchResult):
        """Sonucu panoya kopyala"""
        try:
            content = f"""
{result.title or f'Madde {result.article_number}'}
Belge: {result.document_title}
Tür: {result.document_type}
Skor: {result.score:.3f}
İçerik: {result.content}
"""
            QApplication.clipboard().setText(content.strip())
            
        except Exception as e:
            self.logger.error(f"Panoya kopyalama hatası: {e}")
    
    def add_to_favorites(self, result: SearchResult):
        """Favorilere ekle"""
        try:
            # TODO: Implement favorites functionality
            pass
            
        except Exception as e:
            self.logger.error(f"Favori ekleme hatası: {e}")
    
    def add_note(self, result: SearchResult):
        """Not ekle"""
        try:
            # TODO: Implement note functionality
            pass
            
        except Exception as e:
            self.logger.error(f"Not ekleme hatası: {e}")
    
    def on_selection_changed(self):
        """Seçim değiştiğinde"""
        try:
            current_row = self.currentRow()
            if current_row >= 0 and current_row < len(self.results):
                result = self.results[current_row]
                if result:
                    self.result_selected.emit(result)
                    
        except Exception as e:
            self.logger.error(f"Seçim değişimi hatası: {e}")
        
        # Tablo ayarları
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Sütun genişlikleri
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Tür
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Başlık
        header.setSectionResizeMode(2, QHeaderView.Interactive)       # Belge
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Madde
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Skor
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Durum
        
        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Seçim değişimi
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def display_results(self, results: List[SearchResult]):
        """Sonuçları göster"""
        self.results = results
        
        # Tabloyu temizle
        self.setRowCount(0)
        
        if not results:
            return
        
        # Sonuçları ekle
        self.setRowCount(len(results))
        
        for row, result in enumerate(results):
            try:
                # Tür
                type_item = QTableWidgetItem(result.document_type)
                type_item.setData(Qt.UserRole, result)
                self.setItem(row, 0, type_item)
                
                # Başlık
                title = result.title or f"Madde {result.article_number}"
                title_item = QTableWidgetItem(title)
                self.setItem(row, 1, title_item)
                
                # Belge adı
                doc_title = result.document_title or ""
                if result.law_number:
                    doc_title += f" ({result.law_number})"
                doc_item = QTableWidgetItem(doc_title)
                self.setItem(row, 2, doc_item)
                
                # Madde numarası
                article_item = QTableWidgetItem(str(result.article_number) if result.article_number else "")
                self.setItem(row, 3, article_item)
                
                # Skor
                score_item = QTableWidgetItem(f"{result.score:.3f}")
                self.setItem(row, 4, score_item)
                
                # Durum
                status = ""
                if result.is_repealed:
                    status = "Mülga"
                elif result.is_amended:
                    status = "Değişik"
                else:
                    status = "Aktif"
                
                status_item = QTableWidgetItem(status)
                
                # Renk kodlaması
                if result.is_repealed:
                    status_item.setBackground(QBrush(QColor(255, 200, 200)))  # Kırmızımsı
                elif result.is_amended:
                    status_item.setBackground(QBrush(QColor(255, 255, 200)))  # Sarımsı
                else:
                    status_item.setBackground(QBrush(QColor(200, 255, 200)))  # Yeşilimsi
                
                self.setItem(row, 5, status_item)
                
                # Yüksek skor için vurgulama
                if result.score > 0.8:
                    for col in range(self.columnCount()):
                        item = self.item(row, col)
                        if item:
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
            
            except Exception as e:
                self.logger.error(f"Sonuç gösterme hatası (satır {row}): {e}")
                continue
        
        # İlk sonucu seç
        if results:
            self.selectRow(0)
    
    def on_selection_changed(self):
        """Seçim değiştiğinde"""
        current_row = self.currentRow()
        if current_row >= 0 and current_row < len(self.results):
            result = self.results[current_row]
            self.result_selected.emit(result)
    
    def show_context_menu(self, position):
        """Context menu göster"""
        item = self.itemAt(position)
        if not item:
            return
        
        result = self.results[self.currentRow()]
        
        menu = QMenu(self)
        
        # Kopyala
        copy_action = menu.addAction("📋 İçeriği Kopyala")
        copy_action.triggered.connect(lambda: self.copy_result_content(result))
        
        # Favorilere ekle
        favorite_action = menu.addAction("⭐ Favorilere Ekle")
        favorite_action.triggered.connect(lambda: self.add_to_favorites(result))
        
        # Not ekle
        note_action = menu.addAction("📝 Not Ekle")
        note_action.triggered.connect(lambda: self.add_note(result))
        
        menu.addSeparator()
        
        # Detayları göster
        detail_action = menu.addAction("🔍 Detayları Göster")
        detail_action.triggered.connect(lambda: self.show_details(result))
        
        menu.exec_(self.mapToGlobal(position))
    
    def copy_result_content(self, result: SearchResult):
        """Sonuç içeriğini kopyala"""
        from PyQt5.QtWidgets import QApplication
        
        content = f"""
{result.title or f'Madde {result.article_number}'}
{result.document_title} ({result.law_number})
{result.content}
"""
        QApplication.clipboard().setText(content.strip())
    
    def add_to_favorites(self, result: SearchResult):
        """Favorilere ekle"""
        # TODO: Implement favorites functionality
        pass
    
    def add_note(self, result: SearchResult):
        """Not ekle"""
        # TODO: Implement note functionality
        pass
    
    def show_details(self, result: SearchResult):
        """Detayları göster"""
        self.result_selected.emit(result)

class ResultListWidget(QListWidget):
    """Sonuç liste widget'ı (alternatif görünüm)"""
    
    result_selected = pyqtSignal(SearchResult)
    
    def __init__(self):
        super().__init__()
        self.results: List[SearchResult] = []
        
        self.init_ui()
    
    def init_ui(self):
        """UI'yi oluştur"""
        self.setAlternatingRowColors(True)
        self.itemClicked.connect(self.on_item_clicked)
        
        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def display_results(self, results: List[SearchResult]):
        """Sonuçları göster"""
        try:
            self.clear()
            self.results = results
            
            for result in results:
                item = ResultItem(result)
                self.addItem(item)
            
            self.logger.info(f"{len(results)} sonuç listede gösterildi")
            
        except Exception as e:
            self.logger.error(f"Liste sonuç gösterme hatası: {e}")
    
    def show_context_menu(self, position):
        """Context menu göster"""
        try:
            current_item = self.itemAt(position)
            if not current_item:
                return
            
            result = current_item.data(Qt.UserRole)
            if not result:
                return
            
            menu = QMenu(self)
            
            # Detay göster
            show_action = menu.addAction("Detayları Göster")
            show_action.triggered.connect(lambda: self.result_selected.emit(result))
            
            # Panoya kopyala
            copy_action = menu.addAction("Panoya Kopyala")
            copy_action.triggered.connect(lambda: self.copy_to_clipboard(result))
            
            # Favorilere ekle
            fav_action = menu.addAction("Favorilere Ekle")
            fav_action.triggered.connect(lambda: self.add_to_favorites(result))
            
            # Not ekle
            note_action = menu.addAction("Not Ekle")
            note_action.triggered.connect(lambda: self.add_note(result))
            
            menu.exec_(self.mapToGlobal(position))
            
        except Exception as e:
            self.logger.error(f"Context menu hatası: {e}")
    
    def copy_to_clipboard(self, result: SearchResult):
        """Sonucu panoya kopyala"""
        try:
            content = f"""
{result.title or f'Madde {result.article_number}'}
Belge: {result.document_title}
Tür: {result.document_type}
Skor: {result.score:.3f}
İçerik: {result.content}
"""
            QApplication.clipboard().setText(content.strip())
            
        except Exception as e:
            self.logger.error(f"Panoya kopyalama hatası: {e}")
    
    def add_to_favorites(self, result: SearchResult):
        """Favorilere ekle"""
        try:
            # TODO: Implement favorites functionality
            pass
            
        except Exception as e:
            self.logger.error(f"Favori ekleme hatası: {e}")
    
    def add_note(self, result: SearchResult):
        """Not ekle"""
        try:
            # TODO: Implement note functionality
            pass
            
        except Exception as e:
            self.logger.error(f"Not ekleme hatası: {e}")
    
    def display_results(self, results: List[SearchResult]):
        """Sonuçları göster"""
        self.clear()
        self.results = results
        
        for result in results:
            item = ResultItem(result)
            self.addItem(item)
    
    def on_item_clicked(self, item):
        """Item tıklandığında"""
        result = item.data(Qt.UserRole)
        if result:
            self.result_selected.emit(result)

class ResultWidget(QWidget):
    """Ana sonuç widget'ı"""
    
    result_selected = pyqtSignal(SearchResult)
    add_note_requested = pyqtSignal(SearchResult)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_results: List[SearchResult] = []
        
        self.init_ui()
    
    def init_ui(self):
        """UI'yi oluştur"""
        layout = QVBoxLayout(self)
        
        # Üst panel - görünüm seçenekleri
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Görünüm türü seçimi
        view_label = QLabel("Görünüm:")
        top_layout.addWidget(view_label)
        
        self.table_view_btn = QPushButton("📊 Tablo")
        self.table_view_btn.setCheckable(True)
        self.table_view_btn.setChecked(True)
        self.table_view_btn.clicked.connect(lambda: self.set_view_mode('table'))
        top_layout.addWidget(self.table_view_btn)
        
        self.list_view_btn = QPushButton("📋 Liste")
        self.list_view_btn.setCheckable(True)
        self.list_view_btn.clicked.connect(lambda: self.set_view_mode('list'))
        top_layout.addWidget(self.list_view_btn)
        
        top_layout.addStretch()
        
        # Filtre seçenekleri
        self.show_repealed_cb = QCheckBox("Mülga olanları göster")
        self.show_repealed_cb.setChecked(True)
        self.show_repealed_cb.toggled.connect(self.filter_results)
        top_layout.addWidget(self.show_repealed_cb)
        
        self.show_amended_cb = QCheckBox("Değişiklik olanları göster")
        self.show_amended_cb.setChecked(True)
        self.show_amended_cb.toggled.connect(self.filter_results)
        top_layout.addWidget(self.show_amended_cb)
        
        # Export ve Print butonları
        export_btn = QPushButton("📄 Dışa Aktar")
        export_btn.clicked.connect(self.export_results)
        top_layout.addWidget(export_btn)
        
        print_btn = QPushButton("🖨️ Yazdır")
        print_btn.clicked.connect(self.print_results)
        top_layout.addWidget(print_btn)
        
        layout.addWidget(top_panel)
        
        # Ana görünüm alanı
        self.table_widget = ResultTableWidget()
        self.list_widget = ResultListWidget()
        
        # Başlangıçta tablo görünümünü göster
        self.table_widget.setVisible(True)
        self.list_widget.setVisible(False)
        
        layout.addWidget(self.table_widget)
        layout.addWidget(self.list_widget)
        
        # Alt panel - istatistikler
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stats_label = QLabel("Sonuç bulunamadı")
        self.stats_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        bottom_layout.addWidget(self.stats_label)
        
        bottom_layout.addStretch()
        
        # Sonuç sayısı
        self.result_count_label = QLabel("0 sonuç")
        self.result_count_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        bottom_layout.addWidget(self.result_count_label)
        
        layout.addWidget(bottom_panel)
        
        # Signal bağlantıları
        self.table_widget.result_selected.connect(self.on_result_selected)
        self.list_widget.result_selected.connect(self.on_result_selected)
    
    def on_result_selected(self, result: SearchResult):
        """Sonuç seçildiğinde"""
        try:
            self.result_selected.emit(result)
            self.logger.info(f"Sonuç seçildi: {result.title or result.article_number}")
            
        except Exception as e:
            self.logger.error(f"Sonuç seçim hatası: {e}")
        
        # Ana içerik alanı
        content_frame = QFrame()
        content_frame.setFrameStyle(QFrame.StyledPanel)
        content_layout = QVBoxLayout(content_frame)
        
        # Tablo görünümü
        self.table_widget = ResultTableWidget()
        self.table_widget.result_selected.connect(self.result_selected)
        content_layout.addWidget(self.table_widget)
        
        # Liste görünümü (başlangıçta gizli)
        self.list_widget = ResultListWidget()
        self.list_widget.result_selected.connect(self.result_selected)
        self.list_widget.setVisible(False)
        content_layout.addWidget(self.list_widget)
        
        layout.addWidget(content_frame)
        
        # Alt panel - istatistikler
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.StyledPanel)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(8, 4, 8, 4)
        
        self.stats_label = QLabel("Sonuç bulunamadı")
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        
        # Export butonu
        export_btn = QPushButton("📄 Dışa Aktar")
        export_btn.clicked.connect(self.export_results)
        stats_layout.addWidget(export_btn)
        
        layout.addWidget(stats_frame)
    
    def display_results(self, results: List[SearchResult]):
        """Sonuçları göster"""
        self.current_results = results
        
        # Filtrelenmiş sonuçları al
        filtered_results = self.get_filtered_results()
        
        # Her iki görünümü de güncelle
        self.table_widget.display_results(filtered_results)
        self.list_widget.display_results(filtered_results)
        
        # İstatistikleri güncelle
        self.update_stats(filtered_results)
        
        self.logger.info(f"{len(filtered_results)} sonuç görüntüleniyor")
    
    def get_filtered_results(self) -> List[SearchResult]:
        """Filtrelenmiş sonuçları al"""
        if not self.current_results:
            return []
        
        filtered = []
        
        for result in self.current_results:
            # Mülga filtresi
            if result.is_repealed and not self.show_repealed_cb.isChecked():
                continue
            
            # Değişiklik filtresi  
            if result.is_amended and not self.show_amended_cb.isChecked():
                continue
            
            filtered.append(result)
        
        return filtered
    
    def update_stats(self, results: List[SearchResult]):
        """İstatistikleri güncelle"""
        if not results:
            self.stats_label.setText("Sonuç bulunamadı")
            return
        
        total = len(results)
        
        # Tür dağılımı
        type_counts = {}
        active_count = 0
        repealed_count = 0
        amended_count = 0
        
        for result in results:
            # Tür sayımı
            doc_type = result.document_type
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # Durum sayımı
            if result.is_repealed:
                repealed_count += 1
            elif result.is_amended:
                amended_count += 1
            else:
                active_count += 1
        
        # İstatistik metnini oluştur
        stats_parts = [f"Toplam: {total}"]
        
        if active_count:
            stats_parts.append(f"Aktif: {active_count}")
        if amended_count:
            stats_parts.append(f"Değişik: {amended_count}")
        if repealed_count:
            stats_parts.append(f"Mülga: {repealed_count}")
        
        # En yaygın türü ekle
        if type_counts:
            most_common_type = max(type_counts, key=type_counts.get)
            stats_parts.append(f"En yaygın: {most_common_type} ({type_counts[most_common_type]})")
        
        stats_text = " | ".join(stats_parts)
        self.stats_label.setText(stats_text)
    
    def set_view_mode(self, mode: str):
        """Görünüm modunu ayarla"""
        if mode == 'table':
            self.table_widget.setVisible(True)
            self.list_widget.setVisible(False)
            self.table_view_btn.setChecked(True)
            self.list_view_btn.setChecked(False)
        elif mode == 'list':
            self.table_widget.setVisible(False)
            self.list_widget.setVisible(True)
            self.table_view_btn.setChecked(False)
            self.list_view_btn.setChecked(True)
    
    def filter_results(self):
        """Sonuçları filtrele"""
        filtered_results = self.get_filtered_results()
        
        # Görünümleri güncelle
        self.table_widget.display_results(filtered_results)
        self.list_widget.display_results(filtered_results)
        
        # İstatistikleri güncelle
        self.update_stats(filtered_results)
    
    def export_results(self):
        """Sonuçları dışa aktar"""
        if not self.current_results:
            return
        
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Sonuçları Kaydet",
            f"arama_sonuclari_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                self.save_results_to_file(filename)
                QMessageBox.information(self, "Başarılı", f"Sonuçlar {filename} dosyasına kaydedildi")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosya kaydetme hatası:\n{e}")
    
    def save_results_to_file(self, filename: str):
        """Sonuçları dosyaya kaydet"""
        try:
            filtered_results = self.get_filtered_results()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Arama Sonuçları - {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                f.write("=" * 60 + "\n\n")
                
                for i, result in enumerate(filtered_results, 1):
                    f.write(f"{i}. {result.title or f'Madde {result.article_number}'}\n")
                    f.write(f"   Belge: {result.document_title}\n")
                    if result.law_number:
                        f.write(f"   Kanun No: {result.law_number}\n")
                    f.write(f"   Tür: {result.document_type}\n")
                    f.write(f"   Skor: {result.score:.3f}\n")
                    
                    status = "Aktif"
                    if result.is_repealed:
                        status = "Mülga"
                    elif result.is_amended:
                        status = "Değişik"
                    f.write(f"   Durum: {status}\n")
                    
                    f.write(f"   İçerik: {result.content[:200]}...\n")
                    f.write("-" * 40 + "\n\n")
            
            self.logger.info(f"Sonuçlar {filename} dosyasına kaydedildi")
            
        except Exception as e:
            self.logger.error(f"Sonuç kaydetme hatası: {e}")
            raise
    
    def get_selected_result(self) -> Optional[SearchResult]:
        """Seçili sonucu al"""
        try:
            if self.table_widget.isVisible():
                current_row = self.table_widget.currentRow()
                if current_row >= 0 and current_row < len(self.current_results):
                    return self.current_results[current_row]
            elif self.list_widget.isVisible():
                current_item = self.list_widget.currentItem()
                if current_item:
                    return current_item.data(Qt.UserRole)
            
            return None
    
    def clear_results(self):
        """Sonuçları temizle"""
        try:
            self.current_results = []
            self.table_widget.display_results([])
            self.list_widget.display_results([])
            self.stats_label.setText("Sonuç bulunamadı")
            
            self.logger.info("Sonuçlar temizlendi")
            
        except Exception as e:
            self.logger.error(f"Sonuç temizleme hatası: {e}")
    
    def add_to_favorites(self, result: SearchResult):
        """Favorilere ekle"""
        try:
            # TODO: Implement favorites functionality
            QMessageBox.information(self, "Bilgi", "Favoriler özelliği henüz geliştirilmedi")
            
        except Exception as e:
            self.logger.error(f"Favori ekleme hatası: {e}")
    
    def add_note(self, result: SearchResult):
        """Not ekle"""
        try:
            # TODO: Implement note functionality
            QMessageBox.information(self, "Bilgi", "Not ekleme özelliği henüz geliştirilmedi")
            
        except Exception as e:
            self.logger.error(f"Not ekleme hatası: {e}")
    
    def show_details(self, result: SearchResult):
        """Detayları göster"""
        try:
            self.result_selected.emit(result)
            
        except Exception as e:
                        self.logger.error(f"Detay gösterme hatası: {e}")
    
    def copy_to_clipboard(self, result: SearchResult):
        """Sonucu panoya kopyala"""
        try:
            content = f"""
{result.title or f'Madde {result.article_number}'}
Belge: {result.document_title}
Tür: {result.document_type}
Skor: {result.score:.3f}
İçerik: {result.content}
"""
            QApplication.clipboard().setText(content.strip())
            QMessageBox.information(self, "Başarılı", "Sonuç panoya kopyalandı")
            
        except Exception as e:
            self.logger.error(f"Panoya kopyalama hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Panoya kopyalama hatası:\n{e}")
    
    def save_results_to_file(self, filename: str):
        """Sonuçları dosyaya kaydet"""
        filtered_results = self.get_filtered_results()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Arama Sonuçları - {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, result in enumerate(filtered_results, 1):
                f.write(f"{i}. {result.title or f'Madde {result.article_number}'}\n")
                f.write(f"   Belge: {result.document_title}\n")
                if result.law_number:
                    f.write(f"   Kanun No: {result.law_number}\n")
                f.write(f"   Tür: {result.document_type}\n")
                f.write(f"   Skor: {result.score:.3f}\n")
                
                status = "Aktif"
                if result.is_repealed:
                    status = "Mülga"
                elif result.is_amended:
                    status = "Değişik"
                f.write(f"   Durum: {status}\n")
                
                f.write(f"   İçerik: {result.content[:200]}...\n")
                f.write("-" * 40 + "\n\n")
        
        self.logger.info(f"Sonuçlar {filename} dosyasına kaydedildi")
    
    def get_selected_result(self) -> Optional[SearchResult]:
        """Seçili sonucu al"""
        if self.table_widget.isVisible():
            current_row = self.table_widget.currentRow()
            if current_row >= 0 and current_row < len(self.current_results):
                return self.current_results[current_row]
        elif self.list_widget.isVisible():
            current_item = self.list_widget.currentItem()
            if current_item:
                return current_item.data(Qt.UserRole)
        
        return None
    
    def clear_results(self):
        """Sonuçları temizle"""
        self.current_results = []
        self.table_widget.display_results([])
        self.list_widget.display_results([])
        self.stats_label.setText("Sonuç bulunamadı")
    
    def set_max_results(self, max_count: int):
        """Maksimum sonuç sayısını ayarla"""
        try:
            self.max_results = max_count
            self.logger.info(f"Maksimum sonuç sayısı {max_count} olarak ayarlandı")
        except Exception as e:
            self.logger.error(f"Maksimum sonuç sayısı ayarlama hatası: {e}")
    
    def get_filtered_results(self) -> List[SearchResult]:
        """Filtrelenmiş sonuçları al"""
        if not self.current_results:
            return []
        
        filtered_results = []
        
        for result in self.current_results:
            # Mülga kontrolü
            if not self.show_repealed_cb.isChecked() and result.is_repealed:
                continue
            
            # Değişiklik kontrolü
            if not self.show_amended_cb.isChecked() and result.is_amended:
                continue
            
            filtered_results.append(result)
        
        return filtered_results
    
    def display_results(self, results: List[SearchResult]):
        """Sonuçları göster"""
        try:
            self.current_results = results
            
            # Tablo ve liste görünümlerini güncelle
            self.table_widget.display_results(results)
            self.list_widget.display_results(results)
            
            # İstatistikleri güncelle
            self.update_stats(results)
            
            self.logger.info(f"{len(results)} sonuç gösterildi")
            
        except Exception as e:
            self.logger.error(f"Sonuç gösterme hatası: {e}")
    
    def update_stats(self, results: List[SearchResult]):
        """İstatistikleri güncelle"""
        try:
            if not results:
                self.stats_label.setText("Sonuç bulunamadı")
                return
            
            # Toplam sonuç sayısı
            total_count = len(results)
            
            # Belge türü dağılımı
            type_counts = {}
            for result in results:
                doc_type = result.document_type or "Bilinmeyen"
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            # Durum dağılımı
            active_count = len([r for r in results if not r.is_repealed and not r.is_amended])
            amended_count = len([r for r in results if r.is_amended])
            repealed_count = len([r for r in results if r.is_repealed])
            
            # İstatistik metni oluştur
            stats_parts = [
                f"Toplam: {total_count}",
                f"Aktif: {active_count}",
                f"Değişik: {amended_count}",
                f"Mülga: {repealed_count}"
            ]
            
            # En yaygın türü ekle
            if type_counts:
                most_common_type = max(type_counts, key=type_counts.get)
                stats_parts.append(f"En yaygın: {most_common_type} ({type_counts[most_common_type]})")
            
            stats_text = " | ".join(stats_parts)
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            self.logger.error(f"İstatistik güncelleme hatası: {e}")
            self.stats_label.setText("İstatistik hatası")
    
    def set_view_mode(self, mode: str):
        """Görünüm modunu ayarla"""
        try:
            if mode == 'table':
                self.table_widget.setVisible(True)
                self.list_widget.setVisible(False)
                self.table_view_btn.setChecked(True)
                self.list_view_btn.setChecked(False)
            elif mode == 'list':
                self.table_widget.setVisible(False)
                self.list_widget.setVisible(True)
                self.table_view_btn.setChecked(False)
                self.list_view_btn.setChecked(True)
            
            self.logger.info(f"Görünüm modu {mode} olarak ayarlandı")
            
        except Exception as e:
            self.logger.error(f"Görünüm modu ayarlama hatası: {e}")
    
    def filter_results(self):
        """Sonuçları filtrele"""
        try:
            filtered_results = self.get_filtered_results()
            
            # Görünümleri güncelle
            self.table_widget.display_results(filtered_results)
            self.list_widget.display_results(filtered_results)
            
            # İstatistikleri güncelle
            self.update_stats(filtered_results)
            
            self.logger.info(f"Sonuçlar filtrelendi: {len(filtered_results)} sonuç")
            
        except Exception as e:
            self.logger.error(f"Sonuç filtreleme hatası: {e}")
    
    def export_results(self):
        """Sonuçları dışa aktar"""
        if not self.current_results:
            QMessageBox.warning(self, "Uyarı", "Dışa aktarılacak sonuç bulunamadı")
            return
        
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Sonuçları Kaydet",
                f"arama_sonuclari_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
            )
            
            if filename:
                self.save_results_to_file(filename)
                QMessageBox.information(self, "Başarılı", f"Sonuçlar {filename} dosyasına kaydedildi")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya kaydetme hatası:\n{e}")
    
    def export_to_pdf(self):
        """Sonuçları PDF'e aktar"""
        if not self.current_results:
            QMessageBox.warning(self, "Uyarı", "Dışa aktarılacak sonuç bulunamadı")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "PDF'e Aktar",
                f"arama_sonuclari_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if filename:
                self._create_pdf_report(filename)
                QMessageBox.information(self, "Başarılı", f"PDF raporu {filename} dosyasına kaydedildi")
                
        except ImportError:
            QMessageBox.critical(self, "Hata", "PDF export için reportlab kütüphanesi gerekli")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF export hatası:\n{e}")
    
    def _create_pdf_report(self, filename: str):
        """PDF raporu oluştur"""
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Başlık
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        title = Paragraph(f"Arama Sonuçları Raporu", title_style)
        story.append(title)
        
        # Tarih
        date_style = ParagraphStyle(
            'Date',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1
        )
        date = Paragraph(f"Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style)
        story.append(date)
        story.append(Spacer(1, 20))
        
        # İstatistikler
        filtered_results = self.get_filtered_results()
        stats_text = f"Toplam Sonuç: {len(filtered_results)}"
        stats_para = Paragraph(stats_text, styles['Normal'])
        story.append(stats_para)
        story.append(Spacer(1, 20))
        
        # Tablo başlıkları
        headers = ['Sıra', 'Başlık', 'Belge', 'Tür', 'Skor', 'Durum']
        data = [headers]
        
        # Tablo verileri
        for i, result in enumerate(filtered_results, 1):
            title = result.title or f'Madde {result.article_number}' or 'Başlıksız'
            doc_title = result.document_title or 'Bilinmeyen'
            doc_type = result.document_type or 'Bilinmeyen'
            score = f"{result.score:.3f}"
            
            status = "Aktif"
            if result.is_repealed:
                status = "Mülga"
            elif result.is_amended:
                status = "Değişik"
            
            row = [str(i), title[:30], doc_title[:30], doc_type, score, status]
            data.append(row)
        
        # Tablo oluştur
        table = Table(data, colWidths=[0.5*inch, 2*inch, 2*inch, 1*inch, 0.8*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # PDF oluştur
        doc.build(story)
        self.logger.info(f"PDF raporu oluşturuldu: {filename}")
    
    def print_results(self):
        """Sonuçları yazdır"""
        if not self.current_results:
            QMessageBox.warning(self, "Uyarı", "Yazdırılacak sonuç bulunamadı")
            return
        
        try:
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt5.QtWidgets import QMessageBox
            
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec_() == QPrintDialog.Accepted:
                self._print_results(printer)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yazdırma hatası:\n{e}")
    
    def _print_results(self, printer):
        """Sonuçları yazdır"""
        try:
            from PyQt5.QtGui import QPainter, QFont
            from PyQt5.QtCore import Qt
            
            painter = QPainter()
            if not painter.begin(printer):
                QMessageBox.critical(self, "Hata", "Yazdırma başlatılamadı")
                return
            
            # Font ayarları
            font = QFont("Arial", 10)
            painter.setFont(font)
            
            # Sayfa boyutları
            page_rect = printer.pageRect()
            x = page_rect.x() + 50
            y = page_rect.y() + 50
            line_height = 20
            
            # Başlık
            title = "Arama Sonuçları Raporu"
            painter.drawText(x, y, title)
            y += line_height * 2
            
            # Tarih
            date_text = f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            painter.drawText(x, y, date_text)
            y += line_height * 2
            
            # Sonuçlar
            filtered_results = self.get_filtered_results()
            for i, result in enumerate(filtered_results, 1):
                # Sayfa sonu kontrolü
                if y > page_rect.height() - 100:
                    printer.newPage()
                    y = page_rect.y() + 50
                
                # Sonuç bilgileri
                title = result.title or f'Madde {result.article_number}' or 'Başlıksız'
                painter.drawText(x, y, f"{i}. {title}")
                y += line_height
                
                doc_title = result.document_title or 'Bilinmeyen'
                painter.drawText(x + 20, y, f"Belge: {doc_title}")
                y += line_height
                
                if result.law_number:
                    painter.drawText(x + 20, y, f"Kanun No: {result.law_number}")
                    y += line_height
                
                painter.drawText(x + 20, y, f"Tür: {result.document_type}")
                y += line_height
                
                painter.drawText(x + 20, y, f"Skor: {result.score:.3f}")
                y += line_height
                
                status = "Aktif"
                if result.is_repealed:
                    status = "Mülga"
                elif result.is_amended:
                    status = "Değişik"
                
                painter.drawText(x + 20, y, f"Durum: {status}")
                y += line_height * 2
            
            painter.end()
            QMessageBox.information(self, "Başarılı", "Yazdırma tamamlandı")
            
        except Exception as e:
            self.logger.error(f"Yazdırma hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Yazdırma sırasında hata oluştu:\n{e}")
