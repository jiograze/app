"""
Test script for Tapu ve Kadastro analysis functionality.
"""
import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.legal_analyzer import LegalTextAnalyzer
from app.core.tapu_kadastro import tapu_belgesi_analiz_et, tapu_metninden_ozet_cikar, TAPU_KEYWORDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample tapu document for testing
SAMPLE_TAPU_DOC = """
TAPU KAYIT ÖRNEĞİ

İL: İSTANBUL
İLÇE: KADIKÖY
KÖY/MAHALLE: FENERBAHÇE MAHALLESİ

ADA: 123
PARSEL: 456
PAFTA: 789

NİTELİK: ARSA
YÜZÖLÇÜMÜ: 1000 m²

HUKUKİ DURUM:
- Mülkiyet: Şahıs mülkiyeti
- İrtifak Hakkı: Yok
- Şerh: Hacizli
- İpotek: 500.000 TL

MALİKLER:
1. AHMET YILMAZ - 12345678901 - 1/1 hisse
2. AYŞE YILMAZ - 10987654321 - 1/1 hisse

AÇIKLAMALAR:
- Bu tapu kaydı örnek amaçlıdır.
- 12.05.2023 tarihli 1234 sayılı karara istinaden düzenlenmiştir.
"""

def test_tapu_analysis():
    """Test tapu document analysis functionality."""
    logger.info("Testing tapu document analysis...")
    
    # Initialize the analyzer
    analyzer = LegalTextAnalyzer()
    
    # Analyze the sample document
    result = analyzer.analyze_text(SAMPLE_TAPU_DOC)
    
    # Check basic tapu information
    tapu_analysis = result.tapu_analysis
    assert tapu_analysis["il"] == "İSTANBUL"
    assert tapu_analysis["ilce"] == "KADIKÖY"
    assert tapu_analysis["koy_mahalle"] == "FENERBAHÇE MAHALLESİ"
    assert tapu_analysis["ada_no"] == "123"
    assert tapu_analysis["parsel_no"] == "456"
    assert tapu_analysis["pafta_no"] == "789"
    assert tapu_analysis["nitelik"] == "ARSA"
    assert tapu_analysis["yuzolcum"] == "1000 m²"
    
    # Check if keywords were detected
    assert len(tapu_analysis["anahtar_kelimeler"]) > 0
    
    # Check if summary was generated
    assert "ozet" in tapu_analysis
    assert len(tapu_analysis["ozet"]) > 0
    
    # Check kadastro analysis
    assert result.kadastro_analysis["tapu_ile_iliskili"] is True
    
    logger.info("Tapu analysis test passed successfully!")

def test_tapu_keyword_detection():
    """Test detection of tapu-related keywords."""
    logger.info("Testing tapu keyword detection...")
    
    # Initialize the analyzer
    analyzer = LegalTextAnalyzer()
    
    # Test with a simple text containing tapu keywords
    test_text = "Bu belge tapu sicil müdürlüğü tarafından düzenlenmiştir. Ada 123 parsel 456 no'lu taşınmaz için geçerlidir."
    result = analyzer.analyze_text(test_text)
    
    # Check if tapu-related entities were detected
    tapu_entities = [e for e in result.entities if e.get("tapu_ilgili", False)]
    assert len(tapu_entities) > 0, "No tapu-related entities detected"
    
    # Check if kadastro analysis indicates tapu relation
    assert result.kadastro_analysis["tapu_ile_iliskili"] is True
    
    logger.info("Tapu keyword detection test passed!")

def test_tapu_utility_functions():
    """Test utility functions in tapu_kadastro module."""
    logger.info("Testing tapu utility functions...")
    
    # Test tapu_belgesi_analiz_et
    tapu_bilgisi = tapu_belgesi_analiz_et(SAMPLE_TAPU_DOC)
    assert tapu_bilgisi.il == "İSTANBUL"
    assert tapu_bilgisi.ilce == "KADIKÖY"
    assert tapu_bilgisi.ada_no == "123"
    assert tapu_bilgisi.parsel_no == "456"
    
    # Test tapu_metninden_ozet_cikar
    ozet = tapu_metninden_ozet_cikar(SAMPLE_TAPU_DOC)
    assert isinstance(ozet, str)
    assert len(ozet) > 0
    
    logger.info("Tapu utility functions test passed!")

if __name__ == "__main__":
    try:
        test_tapu_analysis()
        test_tapu_keyword_detection()
        test_tapu_utility_functions()
        print("\nAll tests completed successfully!")
    except AssertionError as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1)
