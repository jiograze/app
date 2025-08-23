"""
Gelişmiş metin analiz ve temizleme modülü
Türkçe hukuki metinler için özelleştirilmiş
"""

import re
import logging
import unicodedata
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TextAnalysisResult:
    """Metin analiz sonucu"""
    original_text: str
    clean_text: str
    normalized_text: str
    keywords: List[str]
    legal_terms: List[str]
    article_numbers: List[str]
    law_references: List[str]
    word_count: int
    sentence_count: int
    readability_score: float
    language: str = 'tr'

class TurkishTextAnalyzer:
    """Türkçe hukuki metin analiz sistemi"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Türkçe karakterler
        self.turkish_chars = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
            'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
        }
        
        # Hukuki terimler sözlüğü
        self.legal_terms = self._load_legal_terms()
        
        # Stop words (yaygın kelimeler)
        self.stop_words = self._load_stop_words()
        
        # Regex patterns
        self.patterns = self._compile_patterns()
    
    def _load_legal_terms(self) -> Set[str]:
        """Hukuki terimler sözlüğünü yükle"""
        terms = {
            # Temel hukuki terimler
            'kanun', 'madde', 'fıkra', 'bent', 'tüzük', 'yönetmelik', 'genelge',
            'kararnâme', 'cumhurbaşkanlığı', 'bakanlar kurulu', 'resmi gazete',
            'anayasa', 'türk ceza kanunu', 'medeni kanun', 'borçlar kanunu',
            'iş kanunu', 'vergi kanunu', 'ticaret kanunu', 'sosyal güvenlik',
            
            # Hukuki kavramlar
            'hak', 'yükümlülük', 'sorumluluk', 'ceza', 'para cezası', 'hapis',
            'tazminat', 'faiz', 'gecikme faizi', 'vade', 'süre', 'müddet',
            'ihbar', 'tebliğ', 'duyuru', 'ilan', 'başvuru', 'dilekçe',
            
            # Kurumsal terimler
            'maliye bakanlığı', 'adalet bakanlığı', 'içişleri bakanlığı',
            'milli eğitim bakanlığı', 'sağlık bakanlığı', 'çevre bakanlığı',
            'gelir idaresi', 'vergi dairesi', 'mahkeme', 'savcılık', 'emniyet',
            
            # Vergi terimleri
            'kdv', 'katma değer vergisi', 'gelir vergisi', 'kurumlar vergisi',
            'damga vergisi', 'harç', 'resim', 'vergi beyannamesi', 'matrah',
            'stopaj', 'tevkifat', 'iade', 'mahsup', 'tahakkuk', 'tahsilat'
        }
        
        return terms
    
    def _load_stop_words(self) -> Set[str]:
        """Türkçe stop words listesi"""
        return {
            've', 'veya', 'ile', 'için', 'olan', 'olarak', 'bu', 'şu', 'o',
            'bir', 'iki', 'üç', 'dört', 'beş', 'altı', 'yedi', 'sekiz', 'dokuz', 'on',
            'da', 'de', 'ta', 'te', 'den', 'dan', 'ten', 'tan', 'la', 'le',
            'ya', 'ye', 'na', 'ne', 'sa', 'se', 'ka', 'ke', 'ga', 'ge',
            'ın', 'in', 'un', 'ün', 'nın', 'nin', 'nun', 'nün',
            'ı', 'i', 'u', 'ü', 'sı', 'si', 'su', 'sü', 'nı', 'ni', 'nu', 'nü',
            'dir', 'dır', 'dur', 'dür', 'tir', 'tır', 'tur', 'tür',
            'mı', 'mi', 'mu', 'mü', 'mıdır', 'midir', 'mudur', 'müdür',
            'her', 'tüm', 'bütün', 'kimi', 'bazı', 'hangi', 'ne', 'nerede',
            'nereye', 'nereden', 'nasıl', 'niçin', 'neden', 'niye', 'kim'
        }
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Regex desenlerini derle"""
        return {
            # Madde numaraları
            'article_numbers': re.compile(
                r'\b(?:madde|md\.?)\s*:?\s*(\d+(?:/\w+)?)\b',
                re.IGNORECASE
            ),
            
            # Kanun numaraları
            'law_numbers': re.compile(
                r'\b(\d{4})\s*sayılı\s*(?:kanun|yasa)\b',
                re.IGNORECASE
            ),
            
            # Kanun atıfları
            'law_references': re.compile(
                r'\b(\d{1,4})\s*sayılı\s*(.+?)\s*(?:kanun|yasa|tüzük|yönetmelik)(?:u|un|ı|in)?\b',
                re.IGNORECASE
            ),
            
            # Tarihler
            'dates': re.compile(
                r'\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b'
            ),
            
            # Resmi Gazete
            'official_gazette': re.compile(
                r'(?:rg|resmi\s*gazete)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{4})\s*-?\s*(\d+)',
                re.IGNORECASE
            ),
            
            # Para miktarları
            'amounts': re.compile(
                r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:tl|türk\s*lirası|lira)\b',
                re.IGNORECASE
            ),
            
            # Yüzdeler
            'percentages': re.compile(
                r'\b(\d+(?:,\d+)?)\s*%\b'
            ),
            
            # Email adresleri
            'emails': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            
            # Temizleme için gereksiz karakterler
            'cleanup_chars': re.compile(
                r'[^\w\s\.\,\;\:\!\?\-\(\)\"\'\/\%]',
                re.UNICODE
            ),
            
            # Çoklu boşluklar
            'multiple_spaces': re.compile(r'\s+'),
            
            # Satır sonları
            'line_breaks': re.compile(r'\n+'),
            
            # Noktalama işaretleri
            'punctuation': re.compile(r'[^\w\s]', re.UNICODE)
        }
    
    def analyze_text(self, text: str) -> TextAnalysisResult:
        """Metni kapsamlı analiz et"""
        try:
            if not text or not text.strip():
                return self._empty_result(text)
            
            # 1. Temel temizlik
            clean_text = self._basic_cleanup(text)
            
            # 2. Normalizasyon
            normalized_text = self._normalize_text(clean_text)
            
            # 3. Anahtar kelime çıkarma
            keywords = self._extract_keywords(normalized_text)
            
            # 4. Hukuki terim tespiti
            legal_terms = self._extract_legal_terms(normalized_text)
            
            # 5. Madde numaraları
            article_numbers = self._extract_article_numbers(text)
            
            # 6. Kanun atıfları
            law_references = self._extract_law_references(text)
            
            # 7. İstatistikler
            word_count = self._count_words(normalized_text)
            sentence_count = self._count_sentences(clean_text)
            readability_score = self._calculate_readability(clean_text)
            
            return TextAnalysisResult(
                original_text=text,
                clean_text=clean_text,
                normalized_text=normalized_text,
                keywords=keywords,
                legal_terms=legal_terms,
                article_numbers=article_numbers,
                law_references=law_references,
                word_count=word_count,
                sentence_count=sentence_count,
                readability_score=readability_score
            )
            
        except Exception as e:
            self.logger.error(f"Metin analiz hatası: {e}")
            return self._empty_result(text)
    
    def _empty_result(self, text: str) -> TextAnalysisResult:
        """Boş analiz sonucu döndür"""
        return TextAnalysisResult(
            original_text=text,
            clean_text="",
            normalized_text="",
            keywords=[],
            legal_terms=[],
            article_numbers=[],
            law_references=[],
            word_count=0,
            sentence_count=0,
            readability_score=0.0
        )
    
    def _basic_cleanup(self, text: str) -> str:
        """Temel metin temizliği"""
        # Unicode normalizasyonu
        text = unicodedata.normalize('NFKC', text)
        
        # Gereksiz karakterleri temizle
        text = self.patterns['cleanup_chars'].sub(' ', text)
        
        # Çoklu boşlukları tek boşluk yap
        text = self.patterns['multiple_spaces'].sub(' ', text)
        
        # Çoklu satır sonlarını tek satır sonu yap
        text = self.patterns['line_breaks'].sub('\n', text)
        
        # Başlangıç ve bitişteki boşlukları temizle
        text = text.strip()
        
        return text
    
    def _normalize_text(self, text: str) -> str:
        """Metni normalize et (arama için optimize)"""
        # Küçük harfe çevir
        text = text.lower()
        
        # Türkçe karakterleri ASCII'ye çevir (arama kolaylığı için)
        for tr_char, ascii_char in self.turkish_chars.items():
            text = text.replace(tr_char.lower(), ascii_char)
        
        # Noktalama işaretlerini temizle
        text = self.patterns['punctuation'].sub(' ', text)
        
        # Çoklu boşlukları temizle
        text = self.patterns['multiple_spaces'].sub(' ', text)
        
        return text.strip()
    
    def _extract_keywords(self, text: str, min_length: int = 3, max_count: int = 50) -> List[str]:
        """Anahtar kelimeleri çıkar"""
        words = text.split()
        
        # Filtreleme
        keywords = []
        word_freq = {}
        
        for word in words:
            if (len(word) >= min_length and 
                word not in self.stop_words and
                word.isalpha()):
                
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Frekansa göre sırala
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_count]]
        
        return keywords
    
    def _extract_legal_terms(self, text: str) -> List[str]:
        """Hukuki terimleri tespit et"""
        found_terms = []
        text_lower = text.lower()
        
        for term in self.legal_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return list(set(found_terms))  # Tekrarları kaldır
    
    def _extract_article_numbers(self, text: str) -> List[str]:
        """Madde numaralarını çıkar"""
        matches = self.patterns['article_numbers'].findall(text)
        return list(set(matches))  # Tekrarları kaldır
    
    def _extract_law_references(self, text: str) -> List[str]:
        """Kanun atıflarını çıkar"""
        references = []
        
        # Sayılı kanun deseni
        matches = self.patterns['law_references'].findall(text)
        for number, name in matches:
            references.append(f"{number} sayılı {name.strip()}")
        
        # Basit sayılı kanun deseni
        simple_matches = self.patterns['law_numbers'].findall(text)
        for number in simple_matches:
            references.append(f"{number} sayılı kanun")
        
        return list(set(references))  # Tekrarları kaldır
    
    def _count_words(self, text: str) -> int:
        """Kelime sayısını hesapla"""
        words = text.split()
        return len([word for word in words if word.isalpha()])
    
    def _count_sentences(self, text: str) -> int:
        """Cümle sayısını hesapla"""
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _calculate_readability(self, text: str) -> float:
        """Okunabilirlik skorunu hesapla (basit metrik)"""
        try:
            word_count = self._count_words(text)
            sentence_count = self._count_sentences(text)
            
            if sentence_count == 0:
                return 0.0
            
            # Ortalama kelime/cümle oranı (basit metrik)
            avg_words_per_sentence = word_count / sentence_count
            
            # 10-15 kelime ideal, daha fazla okunabilirliği düşürür
            if avg_words_per_sentence <= 15:
                return min(100.0, (15 - avg_words_per_sentence + 10) * 5)
            else:
                return max(0.0, 100 - (avg_words_per_sentence - 15) * 2)
                
        except:
            return 0.0
    
    def prepare_for_fts(self, text: str) -> str:
        """FTS5 için metin hazırla"""
        analysis = self.analyze_text(text)
        
        # Hem orijinal hem normalize edilmiş metni birleştir
        # Bu, hem Türkçe karakterli hem de ASCII aramalarını destekler
        fts_text = f"{analysis.clean_text} {analysis.normalized_text}"
        
        # Anahtar kelimeleri ekle (önem artırma için)
        if analysis.keywords:
            fts_text += " " + " ".join(analysis.keywords[:10])
        
        # Hukuki terimleri ekle
        if analysis.legal_terms:
            fts_text += " " + " ".join(analysis.legal_terms)
        
        return fts_text.strip()
    
    def create_search_terms(self, query: str) -> List[str]:
        """Arama sorgusu için alternatif terimler oluştur"""
        terms = []
        
        # Orijinal sorgu
        terms.append(query)
        
        # Normalize edilmiş sorgu
        normalized = self._normalize_text(query)
        if normalized != query:
            terms.append(normalized)
        
        # Kelime kelime normalize
        words = query.split()
        if len(words) > 1:
            normalized_words = [self._normalize_text(word) for word in words]
            terms.append(" ".join(normalized_words))
        
        # Tekrarları kaldır
        return list(set(terms))

class EnhancedFTSQueryBuilder:
    """Gelişmiş FTS5 sorgu oluşturucu"""
    
    def __init__(self, text_analyzer: TurkishTextAnalyzer):
        self.analyzer = text_analyzer
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def build_query(self, user_query: str, search_mode: str = 'comprehensive') -> str:
        """Gelişmiş FTS5 sorgusu oluştur"""
        try:
            if not user_query.strip():
                return '""'
            
            # Analiz et
            analysis = self.analyzer.analyze_text(user_query)
            
            if search_mode == 'exact':
                return self._build_exact_query(user_query)
            elif search_mode == 'phrase':
                return self._build_phrase_query(user_query)
            elif search_mode == 'comprehensive':
                return self._build_comprehensive_query(analysis)
            else:
                return self._build_simple_query(user_query)
                
        except Exception as e:
            self.logger.error(f"FTS sorgu oluşturma hatası: {e}")
            return f'"{user_query}"*'
    
    def _build_exact_query(self, query: str) -> str:
        """Tam eşleşme sorgusu"""
        return f'"{query}"'
    
    def _build_phrase_query(self, query: str) -> str:
        """Phrase (yakınlık) sorgusu"""
        return f'"{query}"'
    
    def _build_simple_query(self, query: str) -> str:
        """Basit prefix sorgusu"""
        words = query.split()
        if len(words) == 1:
            return f'"{words[0]}"*'
        else:
            return ' AND '.join(f'"{word}"*' for word in words if len(word) > 2)
    
    def _build_comprehensive_query(self, analysis: TextAnalysisResult) -> str:
        """Kapsamlı sorgu (hem Türkçe hem normalized)"""
        query_parts = []
        
        # Orijinal kelimeler (yüksek öncelik)
        original_words = analysis.original_text.split()
        if original_words:
            for word in original_words:
                if len(word) > 2:
                    query_parts.append(f'"{word}"*')
        
        # Normalize edilmiş kelimeler (alternatif)
        normalized_words = analysis.normalized_text.split()
        if normalized_words and normalized_words != original_words:
            for word in normalized_words:
                if len(word) > 2 and word not in [w.strip('"*') for w in query_parts]:
                    query_parts.append(f'"{word}"*')
        
        # Hukuki terimler varsa öncelik ver
        if analysis.legal_terms:
            for term in analysis.legal_terms[:3]:  # İlk 3 terimi al
                if term not in analysis.original_text.lower():
                    query_parts.append(f'"{term}"')
        
        if not query_parts:
            return f'"{analysis.original_text}"*'
        
        # OR operatörü ile birleştir (herhangi birinin bulunması yeterli)
        return ' OR '.join(query_parts)
