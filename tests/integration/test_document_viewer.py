"""
Belge Görüntüleme Sistemi Test Dosyası
PDF Viewer ve Document Preview widget'larını test eder
"""

import logging
import os
import sys
from pathlib import Path

# Proje kökünü path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.ui.document_preview_widget import DocumentPreviewWidget
from app.ui.pdf_viewer_widget import PDFViewerWidget
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget


class TestDocumentViewerWindow(QMainWindow):
    """Test penceresi"""

    def __init__(self):
        super().__init__()

        # Logger'ı başlat
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.init_ui()

    def init_ui(self):
        """UI'yi oluştur"""
        self.setWindowTitle("Belge Görüntüleme Sistemi - Test Penceresi")
        self.setGeometry(100, 100, 1200, 800)

        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Ana layout
        main_layout = QVBoxLayout(central_widget)

        # Tab widget
        tab_widget = QTabWidget()

        # PDF Viewer sekmesi
        pdf_viewer_tab = QWidget()
        pdf_viewer_layout = QVBoxLayout(pdf_viewer_tab)

        self.pdf_viewer = PDFViewerWidget()
        self.pdf_viewer.document_loaded.connect(self.on_pdf_loaded)
        pdf_viewer_layout.addWidget(self.pdf_viewer)

        tab_widget.addTab(pdf_viewer_tab, "📄 PDF Viewer")

        # Document Preview sekmesi
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)

        self.document_preview = DocumentPreviewWidget()
        self.document_preview.document_selected.connect(
            self.on_preview_document_selected
        )
        self.document_preview.text_selected.connect(self.on_preview_text_selected)
        preview_layout.addWidget(self.document_preview)

        tab_widget.addTab(preview_tab, "📝 Document Preview")

        main_layout.addWidget(tab_widget)

        # Test verisi yükle
        self.load_test_data()

    def load_test_data(self):
        """Test verisi yükle"""
        try:
            # Örnek belge verisi
            test_document = {
                "id": 1,
                "title": "Test Belgesi - 5651 Sayılı Kanun",
                "document_type": "KANUN",
                "law_number": "5651",
                "content": """
                MADDE 1- Bu Kanunun amacı, internet ortamında yapılan yayınların düzenlenmesi ve bu ortamda işlenen suçlarla mücadele edilmesi ile ilgili esas ve usulleri belirlemektir.

                MADDE 2- Bu Kanun, internet ortamında yapılan yayınlar ile ilgili olarak;
                a) İçerik sağlayıcı, yer sağlayıcı ve toplu kullanım sağlayıcıların yükümlülüklerini,
                b) İçerik, yer ve erişim sağlayıcıları ile toplu kullanım sağlayıcıların sorumluluklarını,
                c) İnternet ortamında yapılan yayınların içeriğine ilişkin düzenlemeleri,
                ç) İnternet ortamında işlenen suçlarla mücadele amacıyla alınacak tedbirleri,
                d) Bu Kanun kapsamında kurulacak kurum ve kuruluşların görev, yetki ve sorumluluklarını,
                e) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirleri,
                f) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasları,
                g) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                ğ) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                h) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                ı) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                i) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                j) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                k) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                l) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                m) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                n) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                o) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                ö) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                p) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                r) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                s) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                ş) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                t) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                u) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                ü) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                v) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                y) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                z) İnternet ortamında yapılan yayınların içeriğine ilişkin olarak alınacak tedbirlerin uygulanmasına ilişkin usul ve esasların belirlenmesi,
                kapsar.
                """,
                "created_at": "2025-01-01",
                "file_path": "/test/path/test_document.pdf",
                "article_count": 25,
                "metadata": {
                    "author": "TBMM",
                    "subject": "İnternet Ortamında Yapılan Yayınların Düzenlenmesi",
                    "creator": "Microsoft Word",
                    "producer": "Microsoft Word",
                    "keywords": "internet, yayın, düzenleme, suç, mücadele",
                },
            }

            # Document Preview'a test verisini yükle
            self.document_preview.load_document(test_document)

            self.logger.info("Test verisi yüklendi")

        except Exception as e:
            self.logger.error(f"Test verisi yükleme hatası: {e}")

    def on_pdf_loaded(self, file_path: str):
        """PDF yüklendiğinde"""
        self.logger.info(f"PDF yüklendi: {file_path}")

    def on_preview_document_selected(self, document_data: dict):
        """Preview'da belge seçildiğinde"""
        self.logger.info(
            f"Preview'da belge seçildi: {document_data.get('title', 'Bilinmeyen')}"
        )

    def on_preview_text_selected(self, selected_text: str):
        """Preview'da metin seçildiğinde"""
        self.logger.info(f"Preview'da metin seçildi: {len(selected_text)} karakter")


def main():
    """Ana fonksiyon"""
    try:
        print("Belge Görüntüleme Sistemi Test Uygulaması başlatılıyor...")

        # Qt uygulamasını başlat
        app = QApplication(sys.argv)

        # Test penceresini oluştur
        test_window = TestDocumentViewerWindow()
        test_window.show()

        print(
            "Test penceresi açıldı. PDF Viewer ve Document Preview widget'larını test edebilirsiniz."
        )
        print("\nKullanım:")
        print("1. PDF Viewer sekmesinde '📁 Aç' butonuna tıklayarak PDF dosyası seçin")
        print("2. Document Preview sekmesinde test belgesini inceleyin")
        print("3. Metin arama özelliğini test edin")

        # Event loop'u başlat
        sys.exit(app.exec_())

    except Exception as e:
        print(f"Test uygulaması başlatılırken hata oluştu: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
