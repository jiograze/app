"""
OCR modülü test scriptı
"""

# Standard library imports
import os
import subprocess
import sys
from pathlib import Path

# Local application imports
from app.core.document_processor import DocumentProcessor
from app.utils.config_manager import ConfigManager
from app.utils.logger import setup_logger

# Third-party imports (none in this file)


# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_tesseract_installation(tesseract_path: str) -> bool:
    """Tesseract kurulumunu ve versiyonunu kontrol eder.

    Args:
        tesseract_path: Tesseract'ın kurulu olduğu yol

    Returns:
        bool: Tesseract düzgün kuruluysa True, değilse False
    """
    if not tesseract_path or not os.path.exists(tesseract_path):
        print(f"❌ Tesseract bulunamadı: {tesseract_path}")
        return False

    print(f"✅ Tesseract bulundu: {tesseract_path}")

    try:
        result = subprocess.run(
            [str(tesseract_path), "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            version_line = result.stdout.split("\n")[0]
            print(f"📦 {version_line}")
            return True
        print("⚠️ Tesseract versiyon alınamadı")
    except Exception as e:
        print(f"⚠️ Tesseract versiyon kontrol hatası: {e}")

    return False


def check_ocr_method(doc_processor) -> bool:
    """OCR metodunun varlığını ve temel işlevselliğini test eder."""
    if not hasattr(doc_processor, "_perform_ocr"):
        print("❌ OCR fonksiyonu bulunamadı")
        return False

    print("✅ OCR fonksiyonu mevcut (_perform_ocr)")
    print("   📋 OCR metodu özellikleri:")

    try:
        dummy_path = Path("test.pdf")
        result = doc_processor._perform_ocr(dummy_path)
        print(f"   ℹ️ Test sonucu (dosya yok): {result}")
        return True
    except Exception as e:
        print(f"   ℹ️ Test exception (normal): {e}")
        return False


def check_ocr_config(ocr_config: dict) -> bool:
    """OCR yapılandırmasını kontrol eder."""
    print("2. OCR konfigürasyon testi...")
    try:
        confidence_threshold = int(ocr_config.get("confidence_threshold", 75))
        if 0 <= confidence_threshold <= 100:
            print(f"   ✅ Güven eşiği geçerli: {confidence_threshold}%")
            return True
        print(f"   ⚠️ Güven eşiği aralık dışı: {confidence_threshold}%")
    except (ValueError, TypeError) as e:
        print(f"   ❌ Geçersiz güven eşiği değeri: {e}")
    except Exception as e:
        print(f"   ❌ Konfigürasyon test hatası: {e}")
    return False


def check_dependencies() -> list:
    """Gerekli Python bağımlılıklarını kontrol eder."""
    print("3. OCR bağımlılıkları kontrol ediliyor...")
    missing_deps = []

    def check_dependency(name: str, import_name: str = None, version_attr: str = None):
        import_name = import_name or name
        try:
            module = __import__(import_name)
            version = getattr(module, version_attr, "") if version_attr else ""
            version_str = f" (v{version}())" if version else ""
            print(f"   ✅ {name} modülü yüklü{version_str}")
        except ImportError:
            missing_deps.append(name)
            print(f"   ❌ {name} modülü bulunamadı")

    check_dependency("pytesseract", version_attr="get_tesseract_version")
    check_dependency("Pillow", "PIL", "__version__")
    check_dependency("pdf2image")

    if missing_deps:
        print(f"   📦 Eksik paketler: {', '.join(missing_deps)}")
        print(f"   💡 Kurulum: pip install {' '.join(missing_deps)}")

    return missing_deps


def test_ocr_module():
    """OCR modülünü test eden ana fonksiyon.

    Returns:
        bool: Tüm testler başarılıysa True, değilse False
    """
    print("🔍 OCR Modülü Test Edilyor...")

    # Yapılandırma yükle
    config = ConfigManager(project_root / "config" / "config.yaml")
    doc_processor = DocumentProcessor(config, None)  # DB olmadan test
    ocr_config = config.get("ocr", {})

    # Yapılandırma bilgilerini göster
    print("📋 OCR Konfigürasyonu:")
    print(f"   - Aktif: {ocr_config.get('enabled', False)}")
    print(f"   - Tesseract Path: {ocr_config.get('tesseract_path', 'Belirtilmemiş')}")
    print(f"   - Dil: {ocr_config.get('lang', 'tur')}")
    print(f"   - Güven Eşiği: {ocr_config.get('confidence_threshold', 75)}%")

    # Testleri çalıştır
    print("\n🧪 OCR Test Senaryoları:")

    # Test 1: OCR metodu kontrolü
    print("1. OCR metodu test ediliyor...")
    ocr_method_ok = check_ocr_method(doc_processor)

    # Test 2: Tesseract kurulumu kontrolü
    tesseract_ok = check_tesseract_installation(ocr_config.get("tesseract_path"))

    # Test 3: Yapılandırma testi
    config_ok = check_ocr_config(ocr_config)

    # Test 4: Bağımlılık kontrolü
    missing_deps = check_dependencies()

    # Sonuçları özetle
    print("\n📊 OCR Test Sonucu:")
    if not ocr_config.get("enabled", False):
        print("ℹ️ OCR config'te devre dışı bırakılmış")
        return False

    all_tests_passed = all([ocr_method_ok, tesseract_ok, config_ok, not missing_deps])
    if all_tests_passed:
        print("✅ OCR tamamen kullanıma hazır!")
    else:
        print("⚠️ OCR eksik bileşenler nedeniyle çalışmayabilir")

    return all_tests_passed


if __name__ == "__main__":
    test_ocr_module()
