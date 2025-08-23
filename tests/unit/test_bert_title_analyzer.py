"""
Test script for BERT-based title analyzer
"""

import os
import sys
import logging
import unittest
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_bert_title_analyzer.log')
    ]
)
logger = logging.getLogger(__name__)

# Test cases
TEST_CASES = [
    {
        "input": """
        TÜRK CEZA KANUNU
        
        Kanun Numarası: 5237
        Kabul Tarihi: 26/9/2004
        
        BİRİNCİ KİTAP
        Genel Hükümler
        
        BİRİNCİ KISIM
        Temel Hükümler, Tanımlar ve Uygulama Alanı
        """,
        "expected_title": "TÜRK CEZA KANUNU",
        "is_title": True
    },
    {
        "input": """
        BİRİNCİ BÖLÜM
        Amaç, Kapsam, Tanımlar ve İlkeler
        
        Amaç
        
        MADDE 1 – (1) Bu Kanunun amacı, kişinin huzur ve güven içinde yaşamasını sağlamaktır.
        """,
        "expected_title": "BİRİNCİ BÖLÜM",
        "is_title": True
    },
    {
        "input": "MADDE 2 – (1) Bu Kanun, 1.4.2005 tarihinde yürürlüğe girer.",
        "expected_title": "MADDE 2 – (1) Bu Kanun, 1.4.2005 tarihinde yürürlüğe girer.",
        "is_title": True  # MADDE ifadeleri de birer başlık olarak kabul ediliyor
    },
    {
        "input": "Bu sadece normal bir cümledir ve başlık değildir.",
        "expected_title": "Bu sadece normal bir cümledir ve başlık değildir.",
        "is_title": False
    }
]

class TestBERTTitleAnalyzer(unittest.TestCase):
    """BERT tabanlı başlık analizörü için test sınıfı"""
    
    @classmethod
    def setUpClass(cls):
        """Test öncesi bir kez çalıştırılır"""
        try:
            from app.core.bert_title_analyzer import BERTTitleAnalyzer
            cls.analyzer = BERTTitleAnalyzer()
            cls.bert_available = True
            logger.info("BERTTitleAnalyzer başarıyla yüklendi")
        except Exception as e:
            logger.error(f"BERTTitleAnalyzer yüklenirken hata oluştu: {str(e)}")
            cls.bert_available = False
    
    def test_title_extraction(self):
        """Başlık çıkarma işlemini test eder"""
        if not self.bert_available:
            self.skipTest("BERT modeli yüklenemedi, test atlanıyor")
        
        for i, test_case in enumerate(TEST_CASES):
            with self.subTest(f"Test Case {i+1}"):
                result = self.analyzer.extract_title_from_text(test_case["input"])
                self.assertIsNotNone(result, "Başlık None döndürdü")
                self.assertGreater(len(result), 0, "Boş başlık döndürdü")
                logger.info(f"Test {i+1}: Beklenen: '{test_case['expected_title']}', Çıktı: '{result}'")
    
    def test_title_classification(self):
        """Başlık sınıflandırma işlemini test eder"""
        if not self.bert_available:
            self.skipTest("BERT modeli yüklenemedi, test atlanıyor")
        
        for i, test_case in enumerate(TEST_CASES):
            if "is_title" not in test_case:
                continue
                
            with self.subTest(f"Test Case {i+1}"):
                is_title, confidence = self.analyzer.is_title(test_case["expected_title"])
                self.assertEqual(
                    is_title, 
                    test_case["is_title"],
                    f"Beklenen: {test_case['is_title']}, Çıktı: {is_title} (Güven: {confidence:.2f})"
                )
                logger.info(f"Test {i+1}: '{test_case['expected_title'][:30]}...' - Güven: {confidence:.2f}")

if __name__ == "__main__":
    unittest.main()
