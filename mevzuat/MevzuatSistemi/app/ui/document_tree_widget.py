"""
Belge ağacı widget'ı - hierarchical belge görüntüleme
"""

import logging
from typing import Dict, List, Optional, Any

from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QComboBox, QMenu, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QTimer
)
from PyQt5.QtGui import QFont, QIcon, QBrush, QColor

class DocumentTreeWidget(QTreeWidget):
    """Belge ağacı widget'ı"""
    
    document_selected = pyqtSignal(dict)  # document_data
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Verileri tut
        self.document_cache: Dict[str, Any] = {}
        
        # Refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # 30 saniye
        
        self.init_ui()
        self.load_documents()
    
    def init_ui(self):
        """UI'yi oluştur"""
        # Başlıklar
        self.setHeaderLabels(["Belge", "Tür", "Madde Sayısı"])
        
        # Ayarlar
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Sütun genişlikleri
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Seçim değişimi
        self.itemClicked.connect(self.on_item_clicked)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
    
    def load_documents(self):
        """Belgeleri veritabanından yükle"""
        try:
            # Mevcut içeriği temizle
            self.clear()
            self.document_cache.clear()
            
            # Belgeleri yükle
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT 
                    d.id,
                    d.title,
                    d.document_type,
                    d.law_number,
                    d.file_path,
                    d.created_at,
                    COUNT(a.id) as article_count,
                    SUM(CASE WHEN a.is_repealed = 1 THEN 1 ELSE 0 END) as repealed_count,
                    SUM(CASE WHEN a.is_amended = 1 THEN 1 ELSE 0 END) as amended_count
                FROM documents d
                LEFT JOIN articles a ON d.id = a.document_id
                GROUP BY d.id
                ORDER BY d.document_type, d.law_number, d.title
            """)
            
            documents = cursor.fetchall()
            cursor.close()
            
            if not documents:
                # Boş mesaj ekle
                no_docs_item = QTreeWidgetItem(["Henüz belge bulunamadı", "", ""])
                no_docs_item.setDisabled(True)
                self.addTopLevelItem(no_docs_item)
                return
            
            # Belgeleri türlere göre grupla
            grouped_docs = {}
            for doc in documents:
                doc_type = doc[2] or "DİĞER"
                if doc_type not in grouped_docs:
                    grouped_docs[doc_type] = []
                grouped_docs[doc_type].append(doc)
            
            # Ağaç yapısını oluştur
            for doc_type, doc_list in grouped_docs.items():
                # Tür başlığı
                type_item = QTreeWidgetItem([f"{doc_type} ({len(doc_list)})", "", ""])
                type_item.setFont(0, QFont("", -1, QFont.Bold))
                type_item.setBackground(0, QBrush(QColor(240, 240, 240)))
                type_item.setData(0, Qt.UserRole, {"type": "category", "category": doc_type})
                
                self.addTopLevelItem(type_item)
                
                # Belgeleri ekle
                for doc in doc_list:
                    doc_data = {
                        "type": "document",
                        "id": doc[0],
                        "title": doc[1],
                        "document_type": doc[2],
                        "law_number": doc[3],
                        "file_path": doc[4],
                        "created_at": doc[5],
                        "article_count": doc[6],
                        "repealed_count": doc[7],
                        "amended_count": doc[8]
                    }
                    
                    # Cache'e ekle
                    self.document_cache[str(doc[0])] = doc_data
                    
                    # Belge adını oluştur
                    doc_title = doc[1] or "Başlıksız Belge"
                    if doc[3]:  # law_number varsa
                        doc_title = f"[{doc[3]}] {doc_title}"
                    
                    # Durum göstergeleri
                    if doc[7] > 0:  # repealed_count
                        doc_title += f" ({doc[7]} mülga)"
                    if doc[8] > 0:  # amended_count
                        doc_title += f" ({doc[8]} değişik)"
                    
                    doc_item = QTreeWidgetItem([
                        doc_title,
                        doc[2] or "",
                        str(doc[6]) if doc[6] else "0"
                    ])
                    
                    doc_item.setData(0, Qt.UserRole, doc_data)
                    
                    # Renk kodlaması
                    if doc[7] > doc[6] / 2:  # Çoğu mülga
                        doc_item.setForeground(0, QBrush(QColor(150, 150, 150)))
                    elif doc[8] > 0:  # Değişiklikler var
                        doc_item.setForeground(0, QBrush(QColor(200, 100, 0)))
                    
                    type_item.addChild(doc_item)
                    
                    # Maddeleri yükle (lazy loading için başta kapalı)
                    if doc[6] > 0:
                        placeholder_item = QTreeWidgetItem(["Maddeler yükleniyor...", "", ""])
                        placeholder_item.setDisabled(True)
                        doc_item.addChild(placeholder_item)
                
                # Türü genişlet
                type_item.setExpanded(True)
            
            self.logger.info(f"{len(documents)} belge ağaç yapısında gösteriliyor")
            
        except Exception as e:
            self.logger.error(f"Belge yükleme hatası: {e}")
            # Hata mesajı ekle
            error_item = QTreeWidgetItem([f"Hata: {e}", "", ""])
            error_item.setDisabled(True)
            self.addTopLevelItem(error_item)
    
    def on_item_clicked(self, item, column):
        """Item tıklandığında"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        
        if data.get("type") == "document":
            # Belge seçildi
            self.document_selected.emit(data)
            
            # Maddeler henüz yüklenmemişse yükle
            if item.childCount() == 1:
                first_child = item.child(0)
                if first_child and first_child.text(0) == "Maddeler yükleniyor...":
                    self.load_articles(item, data["id"])
    
    def on_item_double_clicked(self, item, column):
        """Item çift tıklandığında"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        
        if data.get("type") == "article":
            # Madde seçildi - detay göster
            # TODO: Implement article detail view
            pass
    
    def load_articles(self, doc_item: QTreeWidgetItem, document_id: int):
        """Belgenin maddelerini yükle"""
        try:
            # Placeholder'ı kaldır
            doc_item.removeChild(doc_item.child(0))
            
            # Maddeleri veritabanından al
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT id, article_number, title, content, is_repealed, is_amended
                FROM articles 
                WHERE document_id = ?
                ORDER BY article_number
            """, (document_id,))
            
            articles = cursor.fetchall()
            cursor.close()
            
            if not articles:
                no_articles_item = QTreeWidgetItem(["Madde bulunamadı", "", ""])
                no_articles_item.setDisabled(True)
                doc_item.addChild(no_articles_item)
                return
            
            # Maddeleri ekle
            for article in articles:
                article_data = {
                    "type": "article",
                    "id": article[0],
                    "document_id": document_id,
                    "article_number": article[1],
                    "title": article[2],
                    "content": article[3],
                    "is_repealed": bool(article[4]),
                    "is_amended": bool(article[5])
                }
                
                # Madde başlığı
                article_title = f"Madde {article[1]}"
                if article[2]:
                    article_title += f": {article[2][:50]}"
                    if len(article[2]) > 50:
                        article_title += "..."
                
                # Durum göstergesi
                status = ""
                if article[4]:  # is_repealed
                    status = "Mülga"
                elif article[5]:  # is_amended
                    status = "Değişik"
                else:
                    status = "Aktif"
                
                article_item = QTreeWidgetItem([
                    article_title,
                    status,
                    ""
                ])
                
                article_item.setData(0, Qt.UserRole, article_data)
                
                # Renk kodlaması
                if article[4]:  # Mülga
                    article_item.setForeground(0, QBrush(QColor(150, 150, 150)))
                    article_item.setFont(0, QFont("", -1, QFont.Bold))
                elif article[5]:  # Değişik
                    article_item.setForeground(0, QBrush(QColor(200, 100, 0)))
                
                doc_item.addChild(article_item)
            
            # Belgeyi genişlet
            doc_item.setExpanded(True)
            
            self.logger.info(f"{len(articles)} madde yüklendi (belge: {document_id})")
            
        except Exception as e:
            self.logger.error(f"Madde yükleme hatası: {e}")
            error_item = QTreeWidgetItem([f"Hata: {e}", "", ""])
            error_item.setDisabled(True)
            doc_item.addChild(error_item)
    
    def show_context_menu(self, position):
        """Context menu göster"""
        item = self.itemAt(position)
        if not item:
            return
        
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        
        menu = QMenu(self)
        
        if data.get("type") == "document":
            # Belge işlemleri
            refresh_action = menu.addAction("🔄 Maddeleri Yenile")
            refresh_action.triggered.connect(lambda: self.refresh_document_articles(item, data["id"]))
            
            menu.addSeparator()
            
            show_path_action = menu.addAction("📁 Dosya Yolunu Göster")
            show_path_action.triggered.connect(lambda: self.show_file_path(data))
            
        elif data.get("type") == "article":
            # Madde işlemleri
            copy_action = menu.addAction("📋 İçeriği Kopyala")
            copy_action.triggered.connect(lambda: self.copy_article_content(data))
            
            favorite_action = menu.addAction("⭐ Favorilere Ekle")
            favorite_action.triggered.connect(lambda: self.add_to_favorites(data))
            
        menu.exec_(self.mapToGlobal(position))
    
    def refresh_document_articles(self, doc_item: QTreeWidgetItem, document_id: int):
        """Belgenin maddelerini yenile"""
        # Mevcut maddeleri temizle
        doc_item.takeChildren()
        
        # Placeholder ekle ve maddeleri yeniden yükle
        placeholder_item = QTreeWidgetItem(["Maddeler yenileniyor...", "", ""])
        placeholder_item.setDisabled(True)
        doc_item.addChild(placeholder_item)
        
        self.load_articles(doc_item, document_id)
    
    def show_file_path(self, document_data: dict):
        """Dosya yolunu göster"""
        from PyQt5.QtWidgets import QMessageBox
        
        file_path = document_data.get("file_path", "Bilinmiyor")
        QMessageBox.information(
            self, "Dosya Yolu",
            f"Belge: {document_data.get('title', 'Bilinmiyor')}\n"
            f"Dosya Yolu: {file_path}"
        )
    
    def copy_article_content(self, article_data: dict):
        """Madde içeriğini kopyala"""
        from PyQt5.QtWidgets import QApplication
        
        content = f"Madde {article_data.get('article_number', '')}\n"
        if article_data.get('title'):
            content += f"{article_data['title']}\n"
        content += f"{article_data.get('content', '')}"
        
        QApplication.clipboard().setText(content)
    
    def add_to_favorites(self, article_data: dict):
        """Favorilere ekle"""
        # TODO: Implement favorites functionality
        pass
    
    def refresh_data(self):
        """Verileri yenile"""
        try:
            # Sadece yeni belgeler varsa yenile
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            current_count = cursor.fetchone()[0]
            cursor.close()
            
            # Cache'deki sayı ile karşılaştır
            cached_count = len(self.document_cache)
            
            if current_count != cached_count:
                self.logger.info("Yeni belgeler tespit edildi, ağaç yenileniyor")
                self.load_documents()
                
        except Exception as e:
            self.logger.error(f"Veri yenileme hatası: {e}")
    
    def refresh_tree(self):
        """Ağacı tamamen yenile"""
        try:
            self.logger.info("Belge ağacı yenileniyor...")
            
            # Mevcut cache'i temizle
            self.document_cache.clear()
            
            # Ağacı temizle
            self.clear()
            
            # Belgeleri yeniden yükle
            self.load_documents()
            
            # İstatistikleri güncelle
            self.update_tree_stats()
            
            self.logger.info("Belge ağacı yenilendi")
            
        except Exception as e:
            self.logger.error(f"Ağaç yenileme hatası: {e}")
    
    def auto_refresh(self):
        """Otomatik yenileme"""
        try:
            # Yeni belgeler var mı kontrol et
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM documents 
                WHERE created_at > datetime('now', '-5 minutes')
            """)
            recent_count = cursor.fetchone()[0]
            cursor.close()
            
            if recent_count > 0:
                self.logger.info(f"{recent_count} yeni belge tespit edildi, otomatik yenileme")
                self.refresh_tree()
                
        except Exception as e:
            self.logger.error(f"Otomatik yenileme hatası: {e}")
    
    def update_tree_stats(self):
        """Ağaç istatistiklerini güncelle"""
        try:
            stats = self.get_document_stats()
            
            # Status bar'da göster
            if hasattr(self, 'parent') and hasattr(self.parent(), 'status_bar'):
                status_text = f"Belgeler: {stats['total_documents']} | Maddeler: {stats['total_articles']}"
                self.parent().status_bar.showMessage(status_text, 3000)
            
        except Exception as e:
            self.logger.error(f"İstatistik güncelleme hatası: {e}")
    
    def start_auto_refresh(self, interval_seconds: int = 30):
        """Otomatik yenilemeyi başlat"""
        try:
            if not hasattr(self, 'auto_refresh_timer'):
                self.auto_refresh_timer = QTimer()
                self.auto_refresh_timer.timeout.connect(self.auto_refresh)
            
            self.auto_refresh_timer.start(interval_seconds * 1000)
            self.logger.info(f"Otomatik yenileme başlatıldı ({interval_seconds} saniye)")
            
        except Exception as e:
            self.logger.error(f"Otomatik yenileme başlatma hatası: {e}")
    
    def stop_auto_refresh(self):
        """Otomatik yenilemeyi durdur"""
        try:
            if hasattr(self, 'auto_refresh_timer'):
                self.auto_refresh_timer.stop()
                self.logger.info("Otomatik yenileme durduruldu")
                
        except Exception as e:
            self.logger.error(f"Otomatik yenileme durdurma hatası: {e}")
    
    def search_documents(self, search_text: str):
        """Belgelerde ara"""
        if not search_text:
            # Tüm itemları göster
            for i in range(self.topLevelItemCount()):
                self.setItemHidden(self.topLevelItem(i), False)
            return
        
        search_text = search_text.lower()
        
        # Her üst seviye item'ı kontrol et
        for i in range(self.topLevelItemCount()):
            top_item = self.topLevelItem(i)
            has_match = False
            
            # Alt itemları kontrol et
            for j in range(top_item.childCount()):
                child_item = top_item.child(j)
                item_text = child_item.text(0).lower()
                
                if search_text in item_text:
                    has_match = True
                    self.setItemHidden(child_item, False)
                else:
                    self.setItemHidden(child_item, True)
            
            # Üst item'ı eşleşme durumuna göre göster/gizle
            self.setItemHidden(top_item, not has_match)
            
            if has_match:
                top_item.setExpanded(True)
    
    def get_selected_document(self) -> Optional[dict]:
        """Seçili belgeyi al"""
        current_item = self.currentItem()
        if not current_item:
            return None
        
        data = current_item.data(0, Qt.UserRole)
        if data and data.get("type") == "document":
            return data
        
        return None
    
    def get_document_stats(self) -> dict:
        """Belge istatistiklerini al"""
        stats = {
            "total_documents": 0,
            "total_articles": 0,
            "types": {},
            "status": {"active": 0, "amended": 0, "repealed": 0}
        }
        
        try:
            cursor = self.db.connection.cursor()
            
            # Toplam belgeler
            cursor.execute("SELECT COUNT(*) FROM documents")
            stats["total_documents"] = cursor.fetchone()[0]
            
            # Toplam maddeler
            cursor.execute("SELECT COUNT(*) FROM articles")
            stats["total_articles"] = cursor.fetchone()[0]
            
            # Tür dağılımı
            cursor.execute("""
                SELECT document_type, COUNT(*) 
                FROM documents 
                GROUP BY document_type
            """)
            
            for row in cursor.fetchall():
                doc_type = row[0] or "DİĞER"
                stats["types"][doc_type] = row[1]
            
            # Durum dağılımı
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN is_repealed = 0 AND is_amended = 0 THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN is_amended = 1 THEN 1 ELSE 0 END) as amended,
                    SUM(CASE WHEN is_repealed = 1 THEN 1 ELSE 0 END) as repealed
                FROM articles
            """)
            
            result = cursor.fetchone()
            stats["status"]["active"] = result[0] or 0
            stats["status"]["amended"] = result[1] or 0
            stats["status"]["repealed"] = result[2] or 0
            
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"İstatistik hesaplama hatası: {e}")
        
        return stats

class DocumentTreeContainer(QWidget):
    """Belge ağacı container widget'ı (arama özelliği ile)"""
    
    document_selected = pyqtSignal(dict)
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        """UI'yi oluştur"""
        layout = QVBoxLayout(self)
        
        # Üst panel - arama
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Ara:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Belge adı veya numarası...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        clear_btn = QPushButton("✕")
        clear_btn.setMaximumWidth(30)
        clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_btn)
        
        layout.addLayout(search_layout)
        
        # Ağaç widget'ı
        self.tree_widget = DocumentTreeWidget(self.db)
        self.tree_widget.document_selected.connect(self.document_selected)
        layout.addWidget(self.tree_widget)
        
        # Alt panel - istatistikler
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.stats_label)
        
        # İstatistikleri başlat
        self.update_stats()
        
        # Stats güncelleme timer'ı
        stats_timer = QTimer()
        stats_timer.timeout.connect(self.update_stats)
        stats_timer.start(60000)  # 1 dakika
    
    def on_search_changed(self, text):
        """Arama metni değiştiğinde"""
        self.tree_widget.search_documents(text)
    
    def clear_search(self):
        """Aramayı temizle"""
        self.search_input.clear()
        self.tree_widget.search_documents("")
    
    def update_stats(self):
        """İstatistikleri güncelle"""
        stats = self.tree_widget.get_document_stats()
        
        stats_text = f"Belgeler: {stats['total_documents']} | "
        stats_text += f"Maddeler: {stats['total_articles']} | "
        stats_text += f"Aktif: {stats['status']['active']} | "
        stats_text += f"Değişik: {stats['status']['amended']} | "
        stats_text += f"Mülga: {stats['status']['repealed']}"
        
        self.stats_label.setText(stats_text)
