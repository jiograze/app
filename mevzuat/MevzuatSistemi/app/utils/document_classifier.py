"""
Belge sınıflandırma sınıfı - mevzuat türü ve bilgilerini tespit eder
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

class DocumentClassifier:
    """Belgeleri otomatik olarak sınıflandırır"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Belge türü pattern'leri
        self.document_type_patterns = {
            'ANAYASA': [
                r'(?i)türkiye\s+cumhuriyeti\s+anayasas[ıi]',
                r'(?i)anayasa',
            ],
            'KANUN': [
                r'(?i)(\d+)\s+sayılı\s+.*?kanun',
                r'(?i)kanun\s+no\s*:?\s*(\d+)',
                r'(?i)(\d+)\s+numaralı\s+kanun',
                r'(?i).*?kanunu$'
            ],
            'KHK': [
                r'(?i)(\d+)\s+sayılı\s+.*?kanun\s+hükmünde\s+kararname',
                r'(?i)khk\s+no\s*:?\s*(\d+)',
                r'(?i)kanun\s+hükmünde\s+kararname'
            ],
            'TÜZÜK': [
                r'(?i)tüzük',
                r'(?i)tüzüğü$'
            ],
            'YÖNETMELİK': [
                r'(?i)yönetmelik',
                r'(?i)yönetmeliği$'
            ],
            'YÖNERGE': [
                r'(?i)yönerge',
                r'(?i)genelge'
            ],
            'TEBLİĞ': [
                r'(?i)tebliğ'
            ],
            'KARAR': [
                r'(?i)bakanlar\s+kurulu\s+kararı',
                r'(?i)cumhurbaşkanı\s+kararı',
                r'(?i)karar\s+no'
            ]
        }
        
        # Kanun numarası pattern'leri
        self.law_number_patterns = [
            r'(\d+)\s+sayılı',
            r'kanun\s+no\s*:?\s*(\d+)',
            r'(\d+)\s+numaralı',
            r'no\s*:?\s*(\d+)',
            # Genelge/Yönetmelik formatları
            r'(\d{4}[/-]\d+)',  # 2022/4, 2023-12
            r'sayı\s*:?\s*(\d{4}[/-]\d+)',  # Sayı: 2022/4
            r'genelge\s+no\s*:?\s*(\d{4}[/-]\d+)',  # Genelge No: 2022/4
            r'yönetmelik\s+no\s*:?\s*(\d{4}[/-]\d+)',  # Yönetmelik No: 2022/4
        ]
        
        # Tarih pattern'leri
        self.date_patterns = [
            r'(\d{1,2})[./](\d{1,2})[./](\d{4})',  # dd/mm/yyyy
            r'(\d{4})[./](\d{1,2})[./](\d{1,2})',  # yyyy/mm/dd
            r'(\d{1,2})\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s+(\d{4})'
        ]
        
        # Türkçe aylar
        self.turkish_months = {
            'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
            'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
            'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
        }
    
    def classify_document(self, text: str, filename: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Belgeyi sınıflandır
        
        Args:
            text: Belge metni
            filename: Dosya adı
            metadata: Ek metadata
            
        Returns:
            Sınıflandırma sonucu
        """
        try:
            result = {
                'document_type': 'DIGER',
                'law_number': None,
                'title': '',
                'category': None,
                'subcategory': None,
                'effective_date': None,
                'publication_date': None,
                'confidence': 0.0
            }
            
            # Başlık çıkarma
            title = self._extract_title(text, filename)
            result['title'] = title
            
            # Belge türü tespiti
            doc_type, confidence = self._classify_document_type(text, title, filename)
            result['document_type'] = doc_type
            result['confidence'] = confidence
            
            # Kanun/KHK numarası tespiti
            law_number = None
            if doc_type in ['KANUN', 'KHK', 'YÖNERGE', 'YÖNETMELİK']:
                law_number = self._extract_law_number(text, title, filename)
            
            result['law_number'] = law_number
            
            # Kategori belirleme
            category, subcategory = self._determine_category(text, title, doc_type)
            result['category'] = category
            result['subcategory'] = subcategory
            
            # Tarih bilgileri
            publication_date = self._extract_publication_date(text, metadata)
            effective_date = self._extract_effective_date(text, metadata)
            result['publication_date'] = publication_date
            result['effective_date'] = effective_date
            
            self.logger.info(f"Belge sınıflandırıldı: {doc_type} - {title}")
            return result
            
        except Exception as e:
            self.logger.error(f"Belge sınıflandırma hatası: {e}")
            return {
                'document_type': 'DIGER',
                'title': filename,
                'confidence': 0.0
            }
    
    def _extract_title(self, text: str, filename: str) -> str:
        """Belge başlığını çıkar"""
        # İlk 500 karakterden başlık ara
        first_part = text[:500]
        
        # Yaygın başlık pattern'leri
        title_patterns = [
            r'(?i)^(.+?kanunu?)(?:\s|$)',
            r'(?i)^(.+?kanun\s+hükmünde\s+kararname)(?:\s|$)',
            r'(?i)^(.+?tüzük)(?:\s|$)',
            r'(?i)^(.+?yönetmelik)(?:\s|$)',
            r'(?i)^(.+?yönerge)(?:\s|$)',
            r'(?i)^(.+?tebliğ)(?:\s|$)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, first_part, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Temizle
                title = re.sub(r'\s+', ' ', title)
                title = re.sub(r'[^\w\sÇĞÜŞÖİçğüşöı-]', ' ', title)
                return title.strip()
        
        # Pattern bulunamazsa ilk satırı al
        first_line = text.split('\n')[0].strip()
        if len(first_line) > 10 and len(first_line) < 200:
            return first_line
        
        # Son çare: dosya adından başlık oluştur
        base_name = filename.rsplit('.', 1)[0]
        return base_name.replace('_', ' ').title()
    
    def _classify_document_type(self, text: str, title: str, filename: str) -> tuple:
        """Belge türünü sınıflandır"""
        combined_text = f"{title} {text[:1000]}".lower()
        
        best_type = 'DIGER'
        best_confidence = 0.0
        
        for doc_type, patterns in self.document_type_patterns.items():
            confidence = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    matches += 1
                    confidence += 1.0 / len(patterns)
            
            # Dosya adından da ipucu al
            if doc_type.lower() in filename.lower():
                confidence += 0.3
            
            # Başlıktan da ipucu al
            if doc_type.lower() in title.lower():
                confidence += 0.4
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_type = doc_type
        
        return best_type, min(best_confidence, 1.0)
    
    def _extract_law_number(self, text: str, title: str, filename: str = '') -> Optional[str]:
        """Kanun/KHK/Genelge numarasını çıkar"""
        combined_text = f"{title} {filename} {text[:500]}"
        
        for pattern in self.law_number_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _determine_category(self, text: str, title: str, doc_type: str) -> tuple:
        """Kategori ve alt kategoriyi belirle"""
        # Basit kategorilendirme
        category_keywords = {
            'HUKUK': [
                'medeni', 'borçlar', 'ticaret', 'ceza', 'usul', 'icra', 'iflas',
                'aile', 'miras', 'eşya', 'kişilik', 'sözleşme'
            ],
            'MALIYE': [
                'vergi', 'gümrük', 'bütçe', 'hazine', 'mali', 'gelir', 'kurumlar',
                'katma değer', 'stopaj', 'damga'
            ],
            'İDAREI': [
                'devlet memuru', 'kamu', 'belediye', 'il', 'vali', 'kaymakam',
                'bürokrasi', 'idari'
            ],
            'ÇALIŞMA': [
                'iş', 'işçi', 'sendika', 'toplu iş sözleşmesi', 'sosyal güvenlik',
                'istihdam', 'çalışma'
            ],
            'SAĞLIK': [
                'sağlık', 'tıp', 'hastane', 'doktor', 'eczane', 'ilaç'
            ],
            'EĞİTİM': [
                'eğitim', 'öğretim', 'okul', 'üniversite', 'öğrenci', 'öğretmen'
            ],
            'ÇEVRE': [
                'çevre', 'orman', 'su', 'hava', 'kirlilik', 'atık'
            ]
        }
        
        text_lower = f"{title} {text[:1000]}".lower()
        
        best_category = None
        best_score = 0
        
        for category, keywords in category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_category = category
        
        # Alt kategori belirleme (basit)
        subcategory = None
        if best_category == 'HUKUK':
            if any(word in text_lower for word in ['medeni', 'aile', 'miras']):
                subcategory = 'Medeni Hukuk'
            elif any(word in text_lower for word in ['ceza', 'suç']):
                subcategory = 'Ceza Hukuku'
            elif any(word in text_lower for word in ['ticaret', 'şirket']):
                subcategory = 'Ticaret Hukuku'
        
        return best_category, subcategory
    
    def _extract_publication_date(self, text: str, metadata: Dict = None) -> Optional[str]:
        """Yayın tarihini çıkar"""
        # Metadata'dan önce kontrol et
        if metadata:
            if 'pdf_metadata' in metadata and metadata['pdf_metadata'].get('CreationDate'):
                return metadata['pdf_metadata']['CreationDate']
            if 'core_properties' in metadata and metadata['core_properties'].get('created'):
                return metadata['core_properties']['created']
        
        # Metinden tarih ara
        first_part = text[:1000]
        
        # "yayımlandığı tarih" gibi ifadeler ara
        date_contexts = [
            r'yayımlandığı\s+tarih\s*:?\s*([^,.\n]+)',
            r'yayım\s+tarihi\s*:?\s*([^,.\n]+)',
            r'tarih\s*:?\s*([^,.\n]+)',
            r'(\d{1,2}[./]\d{1,2}[./]\d{4})',
            r'(\d{4}[./]\d{1,2}[./]\d{1,2})'
        ]
        
        for pattern in date_contexts:
            match = re.search(pattern, first_part, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                parsed_date = self._parse_turkish_date(date_str)
                if parsed_date:
                    return parsed_date
        
        return None
    
    def _extract_effective_date(self, text: str, metadata: Dict = None) -> Optional[str]:
        """Yürürlük tarihini çıkar"""
        first_part = text[:1000]
        
        # Yürürlük ifadeleri
        effective_contexts = [
            r'yürürlüğe?\s+(?:gir(?:me|er))\s+tarihi?\s*:?\s*([^,.\n]+)',
            r'yürürlük\s+tarihi?\s*:?\s*([^,.\n]+)',
            r'bu\s+kanun\s+.*?(\d{1,2}[./]\d{1,2}[./]\d{4})',
        ]
        
        for pattern in effective_contexts:
            match = re.search(pattern, first_part, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                parsed_date = self._parse_turkish_date(date_str)
                if parsed_date:
                    return parsed_date
        
        return None
    
    def _parse_turkish_date(self, date_str: str) -> Optional[str]:
        """Türkçe tarih string'ini parse et"""
        try:
            date_str = date_str.lower().strip()
            
            # Sayısal format (dd/mm/yyyy veya yyyy/mm/dd)
            numeric_match = re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', date_str)
            if numeric_match:
                day, month, year = numeric_match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Yyyy/mm/dd format
            numeric_match2 = re.search(r'(\d{4})[./](\d{1,2})[./](\d{1,2})', date_str)
            if numeric_match2:
                year, month, day = numeric_match2.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Türkçe ay isimleri ile
            text_match = re.search(r'(\d{1,2})\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s+(\d{4})', date_str)
            if text_match:
                day, month_name, year = text_match.groups()
                month_num = self.turkish_months.get(month_name)
                if month_num:
                    return f"{year}-{month_num:02d}-{day.zfill(2)}"
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Tarih parse hatası: {date_str} - {e}")
            return None
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Sınıflandırma istatistiklerini döndür"""
        # TODO: Veritabanından gerçek istatistikler
        return {
            'total_classified': 0,
            'by_type': {},
            'accuracy': 0.0
        }
