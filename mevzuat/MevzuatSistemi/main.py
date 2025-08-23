"""
Mevzuat Belge Analiz & Sorgulama Sistemi
Ana uygulama giriş noktası
"""

import sys
import os
from pathlib import Path

# Proje kökünü path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.app_manager import MevzuatApp
from app.utils.logger import setup_logger

def main():
    """Ana uygulama giriş fonksiyonu"""
    try:
        print("Mevzuat Sistemi başlatılıyor...")
        
        # Logger'ı başlat
        logger = setup_logger("mevzuat_main")
        logger.info("Mevzuat Sistemi başlatılıyor...")
        
        print("Logger başlatıldı")
        
        # Ana uygulama nesnesini oluştur ve başlat
        app = MevzuatApp()
        print("App nesnesi oluşturuldu")
        
        app.run()
        
    except Exception as e:
        print(f"Uygulama başlatılırken hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
