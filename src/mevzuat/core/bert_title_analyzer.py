"""
BERT tabanlı başlık analizi modülü
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
import numpy as np

logger = logging.getLogger(__name__)

class BERTTitleAnalyzer:
    """BERT modeli kullanarak belge başlıklarını analiz eden sınıf"""
    
    def __init__(self, model_name: str = "dbmdz/bert-base-turkish-cased", device: str = None):
        """
        BERT tabanlı başlık analizörünü başlatır.
        
        Args:
            model_name: Kullanılacak BERT modelinin adı
            device: Kullanılacak cihaz ('cpu' veya 'cuda')
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        try:
            # Tokenizer ve modeli yükle
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name, 
                num_labels=2  # Başlık/başlık değil sınıflandırması için
            ).to(self.device)
            
            # Pipeline oluştur
            self.classifier = pipeline(
                'text-classification',
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == 'cuda' else -1
            )
            
            logger.info(f"{model_name} modeli başarıyla yüklendi")
        except Exception as e:
            logger.error(f"Model yüklenirken hata oluştu: {str(e)}")
            raise
    
    def is_title(self, text: str, threshold: float = 0.6) -> Tuple[bool, float]:
        """
        Verilen metnin bir başlık olup olmadığını kontrol eder.
        
        Args:
            text: Analiz edilecek metin
            threshold: Başlık olarak kabul edilecek minimum güven skoru (0-1 arası)
            
        Returns:
            Tuple[bool, float]: (Başlık mı?, Güven skoru)
        """
        if not text or len(text.strip()) < 3:
            return False, 0.0
            
        try:
            # Basit kurallar ile ön filtreleme
            text = text.strip()
            
            # Çok uzun metinler başlık olamaz
            if len(text) > 200:
                return False, 0.1
                
            # Başlık olma ihtimali yüksek desenler
            title_patterns = [
                r'^[A-ZĞÜŞİÖÇ][A-ZĞÜŞİÖÇ\s,;:()\-–—"]+$',  # Tümü büyük harf
                r'^[A-ZĞÜŞİÖÇ][a-zçğıöşü]+(?:\s+[A-ZĞÜŞİÖÇa-zçğıöşü]+)*$',  # Başlık formatı
                r'^(?:MADDE|BÖLÜM|KISIM|KANUN|YÖNETMELİK|TÜZÜK|YÖNERGE|TEBLİĞ)\s+[A-Z0-9\-]+',  # Yasal referans
            ]
            
            for pattern in title_patterns:
                if re.match(pattern, text):
                    return True, 0.9  # Yüksek güven
            
            # BERT ile sınıflandırma
            result = self.classifier(text, truncation=True, max_length=128)
            
            # Sonuçları işle
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
                
            if isinstance(result, dict):
                # 'label' anahtarı olup olmadığını kontrol et
                label = result.get('label', 'LABEL_0')
                score = result.get('score', 0.0)
                
                # Eğer model başka bir etiket döndürdüyse, etiketi çevir
                if label == 'LABEL_1':
                    return True, score
                else:
                    return False, 1.0 - score
            
            return False, 0.5
            
        except Exception as e:
            logger.error(f"Başlık analizi sırasında hata: {str(e)}")
            return False, 0.0
    
    def extract_title_from_text(self, text: str, min_length: int = 5, max_length: int = 200) -> Optional[str]:
        """
        Metin içinden en olası başlığı çıkarır.
        
        Args:
            text: İşlenecek metin
            min_length: Minimum başlık uzunluğu (karakter cinsinden)
            max_length: Maksimum başlık uzunluğu (karakter cinsinden)
            
        Returns:
            str: Bulunan başlık veya None
        """
        if not text:
            return None
            
        try:
            # Metni satırlara ayır ve temizle
            lines = []
            for line in text.split('\n'):
                line = line.strip()
                if line and min_length <= len(line) <= max_length:
                    lines.append(line)
            
            if not lines:
                return None
            
            # İlk 10 satırı kontrol et (başlık genellikle üst kısımdadır)
            candidate_lines = lines[:10]
            
            # Her satır için başlık skorunu hesapla
            scored_lines = []
            for line in candidate_lines:
                is_title, score = self.is_title(line)
                if is_title:
                    scored_lines.append((line, score))
            
            # Eğer başlık bulunduysa en yüksek skorlu olanı döndür
            if scored_lines:
                best_line = max(scored_lines, key=lambda x: x[1])
                if best_line[1] > 0.5:  # Minimum güven eşiği
                    return best_line[0]
            
            # Başlık bulunamazsa ilk satırı döndür
            return lines[0] if len(lines[0]) <= max_length else None
            
        except Exception as e:
            logger.error(f"Başlık çıkarılırken hata: {str(e)}")
            # Hata durumunda ilk satırı döndür
            first_line = text.strip().split('\n')[0].strip()
            return first_line if len(first_line) <= max_length else None

    def extract_law_number(self, text: str) -> Optional[str]:
        """
        Metinden kanun numarasını çıkarır.
        
        Args:
            text: İşlenecek metin
            
        Returns:
            str: Bulunan kanun numarası veya None
        """
        # Yaygın kanun numarası formatları
        patterns = [
            r"(?:Kanun No|Sayı|No)[\s:]+(\d+)[\s\-]"  # Kanun No: 1234
            r"(\d+)\s+sayılı\s+kanun",  # 1234 sayılı kanun
            r"(\d+)[\s\-]\d+\s*tarih"  # 1234-5678 sayılı
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
