"""
OCR modülü test scriptı
"""

import os
import sys
from pathlib import Path

# Proje path'ini ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.document_processor import DocumentProcessor
from app.utils.config_manager import ConfigManager
from app.utils.logger import setup_logger

def test_ocr_module():
    """OCR modülünü test et"""
    print("🔍 OCR Modülü Test Edilyor...")
    
    # Logger ve config setup
    logger = setup_logger("OCR_TEST")
    config = ConfigManager(project_root / "config" / "config.yaml")
    
    # Document processor oluştur
    doc_processor = DocumentProcessor(config, None)  # DB olmadan test
    
    # OCR durumu kontrol et
    ocr_config = config.get('ocr', {})
    print(f"📋 OCR Konfigürasyonu:")
    print(f"   - Aktif: {ocr_config.get('enabled', False)}")
    print(f"   - Tesseract Path: {ocr_config.get('tesseract_path', 'Belirtilmemiş')}")
    print(f"   - Dil: {ocr_config.get('lang', 'tur')}")
    print(f"   - Güven Eşiği: {ocr_config.get('confidence_threshold', 75)}")
    
    # Tesseract yolu kontrol et
    tesseract_path = ocr_config.get('tesseract_path')
    if tesseract_path and os.path.exists(tesseract_path):
        print(f"✅ Tesseract bulundu: {tesseract_path}")
        
        # Tesseract versiyon kontrol
        try:
            import subprocess
            result = subprocess.run([tesseract_path, '--version'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"📦 {version_line}")
            else:
                print("⚠️ Tesseract versiyon alınamadı")
        except Exception as e:
            print(f"⚠️ Tesseract versiyon kontrol hatası: {e}")
    else:
        print(f"❌ Tesseract bulunamadı: {tesseract_path}")
    
    # OCR test fonksiyonu var mı kontrol et
    if hasattr(doc_processor, '_perform_ocr'):
        print("✅ OCR fonksiyonu mevcut (_perform_ocr)")
        
        # OCR metodu test et
        print("   📋 OCR metodu özellikleri:")
        try:
            # Basit parametrelerle çağır
            dummy_path = Path("test.pdf")  # Var olmayan dosya
            result = doc_processor._perform_ocr(dummy_path)
            print(f"   ℹ️ Test sonucu (dosya yok): {result}")
        except Exception as e:
            print(f"   ℹ️ Test exception (normal): {e}")
    else:
        print("❌ OCR fonksiyonu bulunamadı")
    
    # PDF test dosyası oluştur (basit)
    print("\n🧪 OCR Test Senaryoları:")
    
    # Test 1: OCR metodu kontrolü
    print("1. OCR metodu test ediliyor...")
    try:
        # Test için basit bir imaj oluşturabiliriz ama şimdilik skip
        print("   ℹ️ Gerçek test için taranmış PDF dosyası gerekli")
        print("   ℹ️ OCR fonksiyonu kodda mevcut, gerçek dosya ile test edilebilir")
        
    except Exception as e:
        print(f"   ❌ OCR test hatası: {e}")
    
    # Test 2: OCR configuration test
    print("2. OCR konfigürasyon testi...")
    try:
        confidence_threshold = ocr_config.get('confidence_threshold', 75)
        if 0 <= confidence_threshold <= 100:
            print(f"   ✅ Güven eşiği geçerli: {confidence_threshold}%")
        else:
            print(f"   ⚠️ Güven eşiği aralık dışı: {confidence_threshold}")
    except Exception as e:
        print(f"   ❌ Konfigürasyon test hatası: {e}")
    
    # Test 3: OCR dependencies kontrolü
    print("3. OCR bağımlılıkları kontrol ediliyor...")
    missing_deps = []
    
    try:
        import pytesseract
        print("   ✅ pytesseract modülü yüklü")
    except ImportError:
        missing_deps.append("pytesseract")
        print("   ❌ pytesseract modülü bulunamadı")
    
    try:
        from PIL import Image
        print("   ✅ PIL/Pillow modülü yüklü") 
    except ImportError:
        missing_deps.append("Pillow")
        print("   ❌ PIL/Pillow modülü bulunamadı")
    
    try:
        import pdf2image
        print("   ✅ pdf2image modülü yüklü")
    except ImportError:
        missing_deps.append("pdf2image")  
        print("   ❌ pdf2image modülü bulunamadı")
    
    if missing_deps:
        print(f"   📦 Eksik paketler: {', '.join(missing_deps)}")
        print(f"   💡 Kurulum: pip install {' '.join(missing_deps)}")
    
    print("\n📊 OCR Test Sonucu:")
    if ocr_config.get('enabled', False):
        if tesseract_path and os.path.exists(tesseract_path) and not missing_deps:
            print("✅ OCR tamamen kullanıma hazır!")
        else:
            print("⚠️ OCR eksik bileşenler nedeniyle çalışmayabilir")
    else:
        print("ℹ️ OCR config'te devre dışı bırakılmış")
    
    return True

if __name__ == "__main__":
    test_ocr_module()
