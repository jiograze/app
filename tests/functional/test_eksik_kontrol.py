#!/usr/bin/env python3
"""
Sistemde eksik kısımları kontrol eden test scripti
"""

import sys
from pathlib import Path

# Proje kökünü path'e ekle
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def test_imports():
    """Import testleri"""
    print("=== IMPORT TESTLERİ ===\n")

    tests = [
        (
            "Core Modules",
            [
                "from app.core.app_manager import MevzuatApp",
                "from app.core.database_manager import DatabaseManager",
                "from app.core.document_processor import DocumentProcessor",
                "from app.core.file_watcher import FileWatcher",
                "from app.core.search_engine import SearchEngine",
            ],
        ),
        (
            "UI Modules",
            [
                "from app.ui.main_window import MainWindow",
                "from app.ui.search_widget import SearchWidget",
                "from app.ui.result_widget import ResultWidget",
                "from app.ui.settings_dialog import SettingsDialog",
            ],
        ),
        (
            "Utils Modules",
            [
                "from app.utils.config_manager import ConfigManager",
                "from app.utils.text_processor import TextProcessor",
                "from app.utils.document_classifier import DocumentClassifier",
                "from app.utils.logger import setup_logger",
            ],
        ),
        (
            "ML Libraries",
            [
                "import numpy",
                "from sentence_transformers import SentenceTransformer",
                "import faiss",
            ],
        ),
    ]

    for category, imports in tests:
        print(f"🔍 {category}:")
        success_count = 0
        for import_stmt in imports:
            try:
                exec(import_stmt)
                print(f"  ✅ {import_stmt}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ {import_stmt} - {e}")

        print(f"  📊 {success_count}/{len(imports)} başarılı\n")


def test_functions():
    """Fonksiyon testleri"""
    print("=== FONKSİYON TESTLERİ ===\n")

    try:
        from app.utils.config_manager import ConfigManager
        from app.utils.text_processor import TextProcessor

        config = ConfigManager()
        tp = TextProcessor(config)

        # Test verileri
        test_text = "MADDE 1 - Bu kanunun amacı mevzuatı düzenlemektir."
        test_slug_text = "5651 Sayılı İnternet Ortamında Yapılan Yayınların Düzenlenmesi Hakkında Kanun"

        print("🔍 Text Processor Fonksiyonları:")

        # clean_text testi
        try:
            cleaned = tp.clean_text(test_text)
            print(f"  ✅ clean_text() - '{cleaned[:30]}...'")
        except Exception as e:
            print(f"  ❌ clean_text() - {e}")

        # slugify testi
        try:
            slug = tp.slugify(test_slug_text)
            print(f"  ✅ slugify() - '{slug}'")
        except Exception as e:
            print(f"  ❌ slugify() - {e}")

        # extract_articles testi
        try:
            articles = tp.extract_articles(test_text)
            print(f"  ✅ extract_articles() - {len(articles)} madde bulundu")
        except Exception as e:
            print(f"  ❌ extract_articles() - {e}")

        print()

    except Exception as e:
        print(f"❌ TextProcessor import hatası: {e}\n")


def test_search_engine():
    """Search engine testleri"""
    print("=== SEARCH ENGINE TESTİ ===\n")

    try:
        from app.core.database_manager import DatabaseManager
        from app.core.search_engine import EMBEDDING_AVAILABLE, SearchEngine
        from app.utils.config_manager import ConfigManager

        print(f"🔍 FAISS/Embedding Durumu:")
        print(f"  EMBEDDING_AVAILABLE: {EMBEDDING_AVAILABLE}")

        if EMBEDDING_AVAILABLE:
            print("  ✅ sentence-transformers ve faiss kullanılabilir")
        else:
            print("  ⚠️  ML kütüphaneleri eksik veya hatalı")

        # Search engine oluşturma testi
        config = ConfigManager()
        db = DatabaseManager(config)

        try:
            search_engine = SearchEngine(config, db)
            print("  ✅ SearchEngine nesnesi oluşturuldu")
        except Exception as e:
            print(f"  ❌ SearchEngine oluşturma hatası: {e}")

        print()

    except Exception as e:
        print(f"❌ Search Engine import hatası: {e}\n")


def test_file_system():
    """Dosya sistemi testleri"""
    print("=== DOSYA SİSTEMİ TESTİ ===\n")

    try:
        from app.utils.config_manager import ConfigManager

        config = ConfigManager()
        base_folder = config.get_base_folder()
        organized_folder = config.get_organized_folder()

        print("🔍 Klasör Yapısı:")
        print(f"  Ana klasör: {base_folder}")
        print(f"  Organize klasör: {organized_folder}")
        print(f"  Ana klasör var: {base_folder.exists()}")
        print(f"  Organize klasör var: {organized_folder.exists()}")

        # Organize klasör içeriği
        if organized_folder.exists():
            subfolders = [p for p in organized_folder.iterdir() if p.is_dir()]
            print(f"  Alt klasörler: {len(subfolders)}")
            for folder in subfolders[:5]:  # İlk 5'ini göster
                print(f"    📁 {folder.name}")

        print()

    except Exception as e:
        print(f"❌ Dosya sistemi testi hatası: {e}\n")


def test_app_creation():
    """Uygulama oluşturma testi"""
    print("=== UYGULAMA OLUŞTURMA TESTİ ===\n")

    try:
        from app.core.app_manager import MevzuatApp

        print("🔍 Ana Uygulama:")
        print("  MevzuatApp oluşturuluyor...")

        # Bu test için GUI başlatmayalım
        import os

        os.environ["QT_QPA_PLATFORM"] = "offscreen"  # Headless mode

        try:
            app = MevzuatApp()
            print("  ✅ MevzuatApp başarıyla oluşturuldu")

            # Bileşen kontrolü
            if hasattr(app, "config") and app.config:
                print("  ✅ Config manager hazır")
            else:
                print("  ❌ Config manager eksik")

            if hasattr(app, "db") and app.db:
                print("  ✅ Database manager hazır")
            else:
                print("  ❌ Database manager eksik")

            if hasattr(app, "document_processor") and app.document_processor:
                print("  ✅ Document processor hazır")
            else:
                print("  ❌ Document processor eksik")

        except Exception as e:
            print(f"  ❌ MevzuatApp oluşturma hatası: {e}")

        print()

    except Exception as e:
        print(f"❌ App creation import hatası: {e}\n")


def main():
    """Ana test fonksiyonu"""
    print("🚀 Mevzuat Sistemi - Eksik Kısım Kontrol Testi\n")
    print("=" * 60 + "\n")

    test_imports()
    test_functions()
    test_search_engine()
    test_file_system()
    test_app_creation()

    print("=" * 60)
    print("🎯 Test tamamlandı!")
    print("\n📊 Sonuç: Yukarıdaki ❌ işaretli kısımlar eksik/hatalı")
    print("✅ işaretli kısımlar çalışıyor durumda")


if __name__ == "__main__":
    main()
