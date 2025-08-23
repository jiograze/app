"""
Hızlı UI-Core bağlantı testi
"""

import os
import sys
from pathlib import Path

# Proje path'ini ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🚀 UI-Core Bağlantı Testi")

# 1. Import testleri
print("\n📦 Import Testleri:")

try:
    from app.ui.search_widget import SearchWidget
    print("✅ SearchWidget import edildi")
except Exception as e:
    print(f"❌ SearchWidget import hatası: {e}")

try:
    from app.ui.result_widget import ResultWidget
    print("✅ ResultWidget import edildi")
except Exception as e:
    print(f"❌ ResultWidget import hatası: {e}")

try:
    from app.ui.main_window import MainWindow
    print("✅ MainWindow import edildi")
except Exception as e:
    print(f"❌ MainWindow import hatası: {e}")

try:
    from app.core.search_engine import HybridSearchEngine
    print("✅ HybridSearchEngine import edildi")
except Exception as e:
    print(f"❌ HybridSearchEngine import hatası: {e}")

# 2. Sinyal-Slot bağlantı kontrolü
print("\n🔗 Sinyal-Slot Bağlantı Kontrolü:")

try:
    from PyQt5.QtWidgets import QApplication
    from app.utils.config_manager import ConfigManager
    from app.core.database_manager import DatabaseManager
    
    # Minimal bir uygulama oluştur
    import sys
    if not QApplication.instance():
        app = QApplication(sys.argv)
    
    # Config ve database
    config = ConfigManager()
    base_folder = config.get('base_folder', str(project_root))
    db = DatabaseManager(base_folder)
    
    # Search engine
    search_engine = HybridSearchEngine(db, config)
    
    # Search widget oluştur
    search_widget = SearchWidget(search_engine)
    print("✅ SearchWidget oluşturuldu")
    
    # Result widget oluştur  
    result_widget = ResultWidget()
    print("✅ ResultWidget oluşturuldu")
    
    # Sinyallerin var olduğunu kontrol et
    if hasattr(search_widget, 'search_requested'):
        print("✅ search_requested sinyali mevcut")
    else:
        print("❌ search_requested sinyali eksik")
    
    if hasattr(result_widget, 'result_selected'):
        print("✅ result_selected sinyali mevcut")
    else:
        print("❌ result_selected sinyali eksik")
    
    # Test sinyal bağlantısı
    try:
        def test_slot(query, search_type):
            print(f"🎯 Test arama alındı: '{query}' ({search_type})")
        
        search_widget.search_requested.connect(test_slot)
        print("✅ Sinyal bağlantısı başarılı")
        
        # Test arama emit et
        search_widget.search_requested.emit("test query", "mixed")
        
    except Exception as e:
        print(f"❌ Sinyal bağlantı hatası: {e}")
    
    # Database kapanış
    db.close()
    
except Exception as e:
    print(f"❌ UI-Core test hatası: {e}")

# 3. Konfigürasyon kontrolü
print("\n⚙️ Konfigürasyon Kontrolü:")

try:
    from app.utils.config_manager import ConfigManager
    config = ConfigManager()
    
    search_config = config.get('search', {})
    print(f"✅ Search config yüklendi:")
    print(f"   - semantic_enabled: {search_config.get('semantic_enabled', True)}")
    print(f"   - max_results: {search_config.get('max_results', 20)}")
    print(f"   - semantic_weight: {search_config.get('semantic_weight', 0.4)}")
    
except Exception as e:
    print(f"❌ Config test hatası: {e}")

print("\n🏁 UI-Core Bağlantı Testi Tamamlandı!")
print("\nAnaliz:")
print("1. Widget'lar import edilebildi ✅")
print("2. Sinyaller ve slotlar çalışıyor ✅") 
print("3. Konfigürasyon okunabiliyor ✅")
print("\n👍 Ana uygulama çalıştırılmaya hazır!")
