"""
İstatistik widget'ı - sistem ve arama istatistikleri
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class StatisticsChart(QWidget):
    """İstatistik grafik widget'ı"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

        if MATPLOTLIB_AVAILABLE:
            self.init_chart()
        else:
            self.init_fallback()

    def init_chart(self):
        """Matplotlib grafik başlat"""
        layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Tema ayarları
        self.figure.patch.set_facecolor("white")

    def init_fallback(self):
        """Matplotlib yoksa basit metin gösterimi"""
        layout = QVBoxLayout(self)

        self.fallback_label = QLabel("Grafik gösterimi için matplotlib gerekli")
        self.fallback_label.setAlignment(Qt.AlignCenter)
        self.fallback_label.setStyleSheet("color: #888; padding: 20px;")
        layout.addWidget(self.fallback_label)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)

    def plot_document_types(self, type_counts: Dict[str, int]):
        """Belge türü dağılımını göster"""
        if not MATPLOTLIB_AVAILABLE:
            self.show_fallback_data("Belge Türü Dağılımı", type_counts)
            return

        if not type_counts:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Pie chart
        labels = list(type_counts.keys())
        sizes = list(type_counts.values())
        colors = plt.cm.Set3(range(len(labels)))

        ax.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
        ax.set_title("Belge Türü Dağılımı")

        self.canvas.draw()

    def plot_search_trends(self, search_data: List[Dict]):
        """Arama trendlerini göster"""
        if not MATPLOTLIB_AVAILABLE:
            self.show_fallback_trends(search_data)
            return

        if not search_data:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Günlük arama sayıları
        dates = [item["date"] for item in search_data]
        counts = [item["count"] for item in search_data]

        ax.plot(dates, counts, marker="o", linewidth=2, markersize=6)
        ax.set_title("Günlük Arama Sayıları")
        ax.set_xlabel("Tarih")
        ax.set_ylabel("Arama Sayısı")
        ax.grid(True, alpha=0.3)

        # Tarih formatı
        self.figure.autofmt_xdate()

        self.canvas.draw()

    def show_fallback_data(self, title: str, data: Dict):
        """Matplotlib olmadığında veri göster"""
        text = f"{title}\n{'=' * len(title)}\n\n"

        for key, value in data.items():
            text += f"{key}: {value}\n"

        self.stats_text.setText(text)

    def show_fallback_trends(self, search_data: List[Dict]):
        """Matplotlib olmadığında trend göster"""
        text = "Arama Trendleri\n===============\n\n"

        for item in search_data:
            text += f"{item['date']}: {item['count']} arama\n"

        self.stats_text.setText(text)


class SystemStatsWidget(QWidget):
    """Sistem istatistikleri widget'ı"""

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        self.init_ui()

    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)

        # Genel istatistikler
        general_group = QGroupBox("Genel İstatistikler")
        general_layout = QGridLayout(general_group)

        # Etiketler
        self.total_docs_label = QLabel("0")
        self.total_articles_label = QLabel("0")
        self.total_searches_label = QLabel("0")
        self.db_size_label = QLabel("0 MB")

        # Grid yerleşimi
        general_layout.addWidget(QLabel("Toplam Belgeler:"), 0, 0)
        general_layout.addWidget(self.total_docs_label, 0, 1)

        general_layout.addWidget(QLabel("Toplam Maddeler:"), 1, 0)
        general_layout.addWidget(self.total_articles_label, 1, 1)

        general_layout.addWidget(QLabel("Toplam Aramalar:"), 2, 0)
        general_layout.addWidget(self.total_searches_label, 2, 1)

        general_layout.addWidget(QLabel("Veritabanı Boyutu:"), 3, 0)
        general_layout.addWidget(self.db_size_label, 3, 1)

        layout.addWidget(general_group)

        # Durum dağılımı
        status_group = QGroupBox("Madde Durumu")
        status_layout = QGridLayout(status_group)

        # Progress bar'lar
        self.active_progress = QProgressBar()
        self.amended_progress = QProgressBar()
        self.repealed_progress = QProgressBar()

        self.active_label = QLabel("0 (0%)")
        self.amended_label = QLabel("0 (0%)")
        self.repealed_label = QLabel("0 (0%)")

        status_layout.addWidget(QLabel("Aktif:"), 0, 0)
        status_layout.addWidget(self.active_progress, 0, 1)
        status_layout.addWidget(self.active_label, 0, 2)

        status_layout.addWidget(QLabel("Değişik:"), 1, 0)
        status_layout.addWidget(self.amended_progress, 1, 1)
        status_layout.addWidget(self.amended_label, 1, 2)

        status_layout.addWidget(QLabel("Mülga:"), 2, 0)
        status_layout.addWidget(self.repealed_progress, 2, 1)
        status_layout.addWidget(self.repealed_label, 2, 2)

        # Progress bar stillerı
        self.active_progress.setStyleSheet(
            """
            QProgressBar::chunk { background-color: #4CAF50; }
        """
        )
        self.amended_progress.setStyleSheet(
            """
            QProgressBar::chunk { background-color: #FF9800; }
        """
        )
        self.repealed_progress.setStyleSheet(
            """
            QProgressBar::chunk { background-color: #F44336; }
        """
        )

        layout.addWidget(status_group)

        # Son işlem bilgileri
        recent_group = QGroupBox("Son İşlemler")
        recent_layout = QVBoxLayout(recent_group)

        self.last_scan_label = QLabel("Henüz tarama yapılmadı")
        self.last_search_label = QLabel("Henüz arama yapılmadı")
        self.last_index_label = QLabel("Henüz indeksleme yapılmadı")

        recent_layout.addWidget(QLabel("Son Tarama:"))
        recent_layout.addWidget(self.last_scan_label)
        recent_layout.addWidget(QLabel("Son Arama:"))
        recent_layout.addWidget(self.last_search_label)
        recent_layout.addWidget(QLabel("Son İndeksleme:"))
        recent_layout.addWidget(self.last_index_label)

        layout.addWidget(recent_group)

        layout.addStretch()

    def update_stats(self):
        """İstatistikleri güncelle"""
        try:
            cursor = self.db.connection.cursor()

            # Temel sayılar
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]
            self.total_docs_label.setText(str(total_docs))

            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            self.total_articles_label.setText(str(total_articles))

            # Arama sayısı (eğer search_history tablosu varsa)
            try:
                cursor.execute("SELECT COUNT(*) FROM search_history")
                total_searches = cursor.fetchone()[0]
                self.total_searches_label.setText(str(total_searches))
            except:
                self.total_searches_label.setText("N/A")

            # Durum dağılımı
            cursor.execute(
                """
                SELECT 
                    SUM(CASE WHEN is_repealed = 0 AND is_amended = 0 THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN is_amended = 1 THEN 1 ELSE 0 END) as amended,
                    SUM(CASE WHEN is_repealed = 1 THEN 1 ELSE 0 END) as repealed
                FROM articles
            """
            )

            result = cursor.fetchone()
            active_count = result[0] or 0
            amended_count = result[1] or 0
            repealed_count = result[2] or 0

            # Progress bar'ları güncelle
            if total_articles > 0:
                active_pct = (active_count / total_articles) * 100
                amended_pct = (amended_count / total_articles) * 100
                repealed_pct = (repealed_count / total_articles) * 100

                self.active_progress.setValue(int(active_pct))
                self.amended_progress.setValue(int(amended_pct))
                self.repealed_progress.setValue(int(repealed_pct))

                self.active_label.setText(f"{active_count} ({active_pct:.1f}%)")
                self.amended_label.setText(f"{amended_count} ({amended_pct:.1f}%)")
                self.repealed_label.setText(f"{repealed_count} ({repealed_pct:.1f}%)")

            # Veritabanı boyutu
            import os

            if hasattr(self.db, "db_path"):
                try:
                    db_size = os.path.getsize(self.db.db_path)
                    db_size_mb = db_size / (1024 * 1024)
                    self.db_size_label.setText(f"{db_size_mb:.1f} MB")
                except:
                    self.db_size_label.setText("N/A")

            cursor.close()

        except Exception as e:
            self.logger.error(f"İstatistik güncelleme hatası: {e}")


class SearchStatsWidget(QWidget):
    """Arama istatistikleri widget'ı"""

    def __init__(self, search_engine):
        super().__init__()
        self.search_engine = search_engine
        self.logger = logging.getLogger(self.__class__.__name__)
        self.init_ui()

    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)

        # Arama performansı
        perf_group = QGroupBox("Arama Performansı")
        perf_layout = QGridLayout(perf_group)

        self.avg_search_time_label = QLabel("0.0 ms")
        self.cache_hit_rate_label = QLabel("0%")
        self.index_size_label = QLabel("0 MB")
        self.semantic_accuracy_label = QLabel("N/A")

        perf_layout.addWidget(QLabel("Ortalama Arama Süresi:"), 0, 0)
        perf_layout.addWidget(self.avg_search_time_label, 0, 1)

        perf_layout.addWidget(QLabel("Cache Hit Oranı:"), 1, 0)
        perf_layout.addWidget(self.cache_hit_rate_label, 1, 1)

        perf_layout.addWidget(QLabel("İndeks Boyutu:"), 2, 0)
        perf_layout.addWidget(self.index_size_label, 2, 1)

        perf_layout.addWidget(QLabel("Semantik Doğruluk:"), 3, 0)
        perf_layout.addWidget(self.semantic_accuracy_label, 3, 1)

        layout.addWidget(perf_group)

        # Popüler aramalar
        popular_group = QGroupBox("Popüler Arama Terimleri")
        popular_layout = QVBoxLayout(popular_group)

        self.popular_table = QTableWidget()
        self.popular_table.setColumnCount(3)
        self.popular_table.setHorizontalHeaderLabels(["Terim", "Sayı", "Son Kullanım"])
        popular_layout.addWidget(self.popular_table)

        layout.addWidget(popular_group)

        # Arama türü dağılımı
        type_group = QGroupBox("Arama Türü Dağılımı")
        type_layout = QGridLayout(type_group)

        self.keyword_count_label = QLabel("0")
        self.semantic_count_label = QLabel("0")
        self.mixed_count_label = QLabel("0")

        type_layout.addWidget(QLabel("Anahtar Kelime:"), 0, 0)
        type_layout.addWidget(self.keyword_count_label, 0, 1)

        type_layout.addWidget(QLabel("Semantik:"), 1, 0)
        type_layout.addWidget(self.semantic_count_label, 1, 1)

        type_layout.addWidget(QLabel("Karma:"), 2, 0)
        type_layout.addWidget(self.mixed_count_label, 2, 1)

        layout.addWidget(type_group)

        layout.addStretch()

    def update_stats(self):
        """Arama istatistiklerini güncelle"""
        try:
            # Search engine'den istatistikleri al
            stats = self.search_engine.get_performance_stats()

            # Performance istatistikleri
            if "avg_search_time" in stats:
                avg_time = stats["avg_search_time"] * 1000  # seconds to ms
                self.avg_search_time_label.setText(f"{avg_time:.1f} ms")

            if "cache_hit_rate" in stats:
                hit_rate = stats["cache_hit_rate"] * 100
                self.cache_hit_rate_label.setText(f"{hit_rate:.1f}%")

            # İndeks boyutu
            if (
                hasattr(self.search_engine, "faiss_index")
                and self.search_engine.faiss_index
            ):
                # FAISS indeks boyutunu tahmin et
                index_size = (
                    self.search_engine.faiss_index.ntotal * 384 * 4
                )  # 384 dim, float32
                index_size_mb = index_size / (1024 * 1024)
                self.index_size_label.setText(f"{index_size_mb:.1f} MB")

            # Popüler aramalar
            if "popular_terms" in stats:
                self.update_popular_terms(stats["popular_terms"])

            # Arama türü sayıları
            if "search_type_counts" in stats:
                counts = stats["search_type_counts"]
                self.keyword_count_label.setText(str(counts.get("keyword", 0)))
                self.semantic_count_label.setText(str(counts.get("semantic", 0)))
                self.mixed_count_label.setText(str(counts.get("mixed", 0)))

        except Exception as e:
            self.logger.error(f"Arama istatistik güncelleme hatası: {e}")

    def update_popular_terms(self, popular_terms: List[Dict]):
        """Popüler terimleri güncelle"""
        self.popular_table.setRowCount(len(popular_terms))

        for row, term_data in enumerate(popular_terms):
            term_item = QTableWidgetItem(term_data.get("term", ""))
            count_item = QTableWidgetItem(str(term_data.get("count", 0)))
            last_used_item = QTableWidgetItem(term_data.get("last_used", ""))

            self.popular_table.setItem(row, 0, term_item)
            self.popular_table.setItem(row, 1, count_item)
            self.popular_table.setItem(row, 2, last_used_item)


class StatsWidget(QWidget):
    """Ana istatistik widget'ı"""

    def __init__(self, db, search_engine):
        super().__init__()
        self.db = db
        self.search_engine = search_engine
        self.logger = logging.getLogger(self.__class__.__name__)

        # Güncelleme timer'ı
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_stats)
        self.update_timer.start(30000)  # 30 saniye

        self.init_ui()
        self.refresh_stats()

    def init_ui(self):
        """UI oluştur"""
        layout = QVBoxLayout(self)

        # Tab widget
        self.tab_widget = QTabWidget()

        # Sistem istatistikleri sekmesi
        self.system_stats = SystemStatsWidget(self.db)
        self.tab_widget.addTab(self.system_stats, "📊 Sistem")

        # Arama istatistikleri sekmesi
        self.search_stats = SearchStatsWidget(self.search_engine)
        self.tab_widget.addTab(self.search_stats, "🔍 Arama")

        # Grafik sekmesi
        self.chart_widget = StatisticsChart()
        self.tab_widget.addTab(self.chart_widget, "📈 Grafikler")

        layout.addWidget(self.tab_widget)

        # Alt panel - kontroller
        controls_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh_stats)
        controls_layout.addWidget(refresh_btn)

        controls_layout.addStretch()

        export_btn = QPushButton("📄 Rapor Oluştur")
        export_btn.clicked.connect(self.export_report)
        controls_layout.addWidget(export_btn)

        layout.addLayout(controls_layout)

    def refresh_stats(self):
        """Tüm istatistikleri yenile"""
        try:
            self.system_stats.update_stats()
            self.search_stats.update_stats()
            self.update_charts()

        except Exception as e:
            self.logger.error(f"İstatistik yenileme hatası: {e}")

    def update_charts(self):
        """Grafikleri güncelle"""
        try:
            # Belge türü dağılımını al
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                SELECT document_type, COUNT(*) 
                FROM documents 
                WHERE document_type IS NOT NULL
                GROUP BY document_type
            """
            )

            type_counts = {}
            for row in cursor.fetchall():
                type_counts[row[0]] = row[1]

            cursor.close()

            # Grafiği güncelle
            if type_counts:
                self.chart_widget.plot_document_types(type_counts)

        except Exception as e:
            self.logger.error(f"Grafik güncelleme hatası: {e}")

    def export_report(self):
        """İstatistik raporu oluştur"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "İstatistik Raporu Kaydet",
            f"mevzuat_istatistik_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)",
        )

        if filename:
            try:
                self.save_report_to_file(filename)
                QMessageBox.information(
                    self, "Başarılı", f"Rapor {filename} dosyasına kaydedildi"
                )
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Rapor kaydetme hatası:\n{e}")

    def save_report_to_file(self, filename: str):
        """Raporu dosyaya kaydet"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Mevzuat Sistemi İstatistik Raporu\n")
            f.write(
                f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            )
            f.write("=" * 60 + "\n\n")

            # Sistem istatistikleri
            f.write("SİSTEM İSTATİSTİKLERİ\n")
            f.write("-" * 30 + "\n")
            f.write(f"Toplam Belgeler: {self.system_stats.total_docs_label.text()}\n")
            f.write(
                f"Toplam Maddeler: {self.system_stats.total_articles_label.text()}\n"
            )
            f.write(
                f"Toplam Aramalar: {self.system_stats.total_searches_label.text()}\n"
            )
            f.write(f"Veritabanı Boyutu: {self.system_stats.db_size_label.text()}\n\n")

            # Madde durumu
            f.write("MADDE DURUMU\n")
            f.write("-" * 20 + "\n")
            f.write(f"Aktif: {self.system_stats.active_label.text()}\n")
            f.write(f"Değişik: {self.system_stats.amended_label.text()}\n")
            f.write(f"Mülga: {self.system_stats.repealed_label.text()}\n\n")

            # Arama performansı
            f.write("ARAMA PERFORMANSI\n")
            f.write("-" * 25 + "\n")
            f.write(
                f"Ortalama Arama Süresi: {self.search_stats.avg_search_time_label.text()}\n"
            )
            f.write(
                f"Cache Hit Oranı: {self.search_stats.cache_hit_rate_label.text()}\n"
            )
            f.write(f"İndeks Boyutu: {self.search_stats.index_size_label.text()}\n\n")

        self.logger.info(f"İstatistik raporu kaydedildi: {filename}")
