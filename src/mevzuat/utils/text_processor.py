"""
Metin işleme yardımcı sınıfı - madde ayırma, temizleme, vb.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple


class TextProcessor:
    """Mevzuat metinlerini işlemek için yardımcı sınıf"""

    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)

        # Madde pattern'leri
        self.article_patterns = [
            r"MADDE\s+(\d+)\s*[-–—]\s*(.*?)(?=MADDE\s+\d+|$)",  # MADDE 1 - Başlık
            r"Madde\s+(\d+)\s*[-–—]\s*(.*?)(?=Madde\s+\d+|$)",  # Madde 1 - Başlık
            r"(\d+)\.\s*MADDE\s*[-–—]\s*(.*?)(?=\d+\.\s*MADDE|$)",  # 1. MADDE - Başlık
            r"(\d+)\.\s*Madde\s*[-–—]\s*(.*?)(?=\d+\.\s*Madde|$)",  # 1. Madde - Başlık
        ]

        # Mülga pattern'leri
        self.repeal_patterns = [
            r"(?i)mülga(?:dır)?",
            r"(?i)yürürlük(?:ten)?\s+kalkmış(?:tır)?",
            r"(?i)iptal\s+edilmiş(?:tir)?",
            r"(?i)kaldırılmış(?:tır)?",
        ]

        # Değişiklik pattern'leri
        self.amendment_patterns = [
            r"(?i)değiş(?:tiril|en)(?:miş(?:tir)?)?",
            r"(?i)eklen(?:miş(?:tir)?)?",
            r"(?i)eklenen",
            r"(?i)yeniden\s+düzenlen(?:miş(?:tir)?)?",
            r"(?i)tadil\s+edilmiş(?:tir)?",
        ]

        # Türkçe karakter dönüşüm tablosu
        self.turkish_char_map = {
            "ı": "i",
            "ş": "s",
            "ç": "c",
            "ö": "o",
            "ğ": "g",
            "ü": "u",
            "İ": "I",
            "Ş": "S",
            "Ç": "C",
            "Ö": "O",
            "Ğ": "G",
            "Ü": "U",
        }

    def extract_articles(self, text: str) -> List[Dict[str, Any]]:
        """
        Metnden maddeleri ayıkla

        Args:
            text: İşlenecek metin

        Returns:
            Madde listesi
        """
        articles = []

        try:
            # Metni temizle
            clean_text = self._preprocess_text(text)

            # Farklı pattern'lerle dene
            for pattern in self.article_patterns:
                matches = re.finditer(pattern, clean_text, re.MULTILINE | re.DOTALL)

                for match in matches:
                    article_number = match.group(1)
                    article_content = match.group(2).strip()

                    # Başlık ve içerik ayırma
                    title, content = self._split_title_content(article_content)

                    # Fıkralara böl
                    paragraphs = self._extract_paragraphs(content)

                    article = {
                        "number": article_number,
                        "title": title,
                        "content": content,
                        "paragraphs": paragraphs,
                        "raw_text": match.group(0),
                    }

                    articles.append(article)

                # Eğer maddeler bulunmuşsa diğer pattern'leri deneme
                if articles:
                    break

            # Eğer hiç madde bulunamadıysa, tüm metni tek madde olarak al
            if not articles:
                articles = [
                    {
                        "number": "1",
                        "title": "Genel",
                        "content": clean_text[:2000],  # İlk 2000 karakter
                        "paragraphs": [clean_text],
                        "raw_text": clean_text,
                    }
                ]

            # Sıralama
            articles.sort(
                key=lambda x: int(x["number"]) if x["number"].isdigit() else 999
            )

            self.logger.info(f"Toplam {len(articles)} madde ayıklandı")
            return articles

        except Exception as e:
            self.logger.error(f"Madde ayıklama hatası: {e}")
            return []

    def _preprocess_text(self, text: str) -> str:
        """Metni ön işleme"""
        # Gereksiz boşlukları temizle
        text = re.sub(r"\s+", " ", text)

        # Sayfa sonları ve gereksiz karakterleri temizle
        text = re.sub(r"[\f\v\r]", "\n", text)
        text = re.sub(r"\n+", "\n", text)

        # Özel karakterleri normalize et
        text = text.replace("–", "-").replace("—", "-")

        return text.strip()

    def _split_title_content(self, article_text: str) -> Tuple[str, str]:
        """Madde başlığını ve içeriğini ayır"""
        lines = article_text.split("\n")

        if len(lines) > 1:
            # İlk satır genellikle başlık
            title = lines[0].strip()
            content = "\n".join(lines[1:]).strip()

            # Başlık çok uzunsa (>100 karakter) tamamını içerik olarak al
            if len(title) > 100:
                title = title[:50] + "..."
                content = article_text
        else:
            # Tek satır - başlık/içerik ayrımı yap
            if len(article_text) > 100:
                title = article_text[:50] + "..."
                content = article_text
            else:
                title = ""
                content = article_text

        return title, content

    def _extract_paragraphs(self, content: str) -> List[str]:
        """İçeriği fıkralara böl"""
        # Fıkra pattern'leri
        paragraph_patterns = [
            r"\(\s*\d+\s*\)",  # (1), (2) şeklinde
            r"\d+\s*\)",  # 1), 2) şeklinde
            r"[a-z]\)",  # a), b) şeklinde
        ]

        paragraphs = []

        # En yaygın pattern ile böl
        for pattern in paragraph_patterns:
            if re.search(pattern, content):
                parts = re.split(pattern, content)
                paragraphs = [p.strip() for p in parts if p.strip()]
                break

        # Eğer fıkra bulunamazsa, nokta ile böl
        if not paragraphs:
            sentences = content.split(".")
            paragraphs = [s.strip() + "." for s in sentences if s.strip()]

        return paragraphs

    def detect_amendments(self, text: str) -> Dict[str, Any]:
        """Mülga ve değişiklik durumunu tespit et"""
        result = {"is_repealed": False, "is_amended": False, "amendment_info": None}

        text_lower = text.lower()

        # Mülga kontrolü
        for pattern in self.repeal_patterns:
            if re.search(pattern, text_lower):
                result["is_repealed"] = True
                result["amendment_info"] = "Mülga"
                break

        # Değişiklik kontrolü (mülga değilse)
        if not result["is_repealed"]:
            for pattern in self.amendment_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    result["is_amended"] = True
                    result["amendment_info"] = f"Değişiklik: {match.group(0)}"
                    break

        return result

    def clean_text(self, text: str) -> str:
        """Metni arama için temizle"""
        if not text:
            return ""

        # Küçük harfe çevir
        text = text.lower()

        # Özel karakterleri temizle
        text = re.sub(r"[^\w\s]", " ", text)

        # Fazla boşlukları temizle
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def slugify(self, text: str) -> str:
        """URL/dosya adı için slug oluştur"""
        if not text:
            return ""

        # Türkçe karakterleri değiştir
        for tr_char, en_char in self.turkish_char_map.items():
            text = text.replace(tr_char, en_char)

        # Küçük harfe çevir
        text = text.lower()

        # Alfanumerik olmayan karakterleri alt çizgi yap
        text = re.sub(r"[^a-z0-9]+", "_", text)

        # Başındaki/sonundaki alt çizgileri temizle
        text = text.strip("_")

        # Uzunluğu sınırla
        return text[:60]

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Metinden anahtar kelimeler çıkar"""
        if not text:
            return []

        # Basit anahtar kelime çıkarma
        # TODO: TF-IDF veya diğer gelişmiş yöntemler

        # Temizle
        clean = self.clean_text(text)

        # Kelimelere böl
        words = clean.split()

        # Stop words (Türkçe)
        stop_words = {
            "bir",
            "bu",
            "ve",
            "ile",
            "için",
            "olan",
            "olarak",
            "her",
            "çok",
            "daha",
            "en",
            "de",
            "da",
            "ki",
            "mi",
            "mu",
            "mı",
            "şu",
            "o",
            "bu",
            "şey",
            "gibi",
            "kadar",
            "sonra",
            "önce",
            "üzere",
            "göre",
            "karşı",
            "dolayı",
            "rağmen",
            "beri",
        }

        # Stop words'leri filtrele ve en az 3 karakterli kelimeleri al
        filtered_words = [
            word for word in words if len(word) >= 3 and word not in stop_words
        ]

        # Kelime sıklığı
        word_count = {}
        for word in filtered_words:
            word_count[word] = word_count.get(word, 0) + 1

        # Sıklığa göre sırala ve ilk N'i al
        keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)

        return [word for word, count in keywords[:max_keywords]]

    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """Metin istatistikleri"""
        if not text:
            return {}

        words = text.split()
        sentences = text.split(".")
        paragraphs = text.split("\n")

        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "paragraph_count": len([p for p in paragraphs if p.strip()]),
            "average_word_length": (
                sum(len(word) for word in words) / len(words) if words else 0
            ),
            "average_sentence_length": len(words) / len(sentences) if sentences else 0,
        }

    def clean_text(self, text: str) -> str:
        """
        Metni temizle ve normalize et

        Args:
            text: Temizlenecek metin

        Returns:
            Temizlenmiş metin
        """
        if not text:
            return ""

        # Fazla boşlukları temizle
        text = re.sub(r"\s+", " ", text)

        # Kontrol karakterlerini temizle
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

        # Fazla noktalama işaretlerini temizle
        text = re.sub(r"[.]{2,}", ".", text)
        text = re.sub(r"[!]{2,}", "!", text)
        text = re.sub(r"[?]{2,}", "?", text)

        # Başlangıç ve bitişteki boşlukları temizle
        text = text.strip()

        return text

    def slugify(self, text: str) -> str:
        """
        Metni URL/dosya adı dostu formata çevir

        Args:
            text: Dönüştürülecek metin

        Returns:
            Slug formatında metin
        """
        if not text:
            return ""

        # Küçük harfe çevir
        text = text.lower()

        # Türkçe karakterleri değiştir
        for tr_char, en_char in self.turkish_char_map.items():
            text = text.replace(tr_char, en_char)

        # Özel karakterleri temizle, sadece harf, rakam ve boşluk bırak
        text = re.sub(r"[^\w\s-]", "", text)

        # Birden fazla boşluğu tek boşlukla değiştir
        text = re.sub(r"\s+", " ", text)

        # Boşlukları alt çizgi ile değiştir
        text = text.replace(" ", "_")

        # Art arda gelen alt çizgileri tek alt çizgiyle değiştir
        text = re.sub(r"_+", "_", text)

        # Başında ve sonundaki alt çizgileri temizle
        text = text.strip("_")

        # Uzunluk sınırı (dosya yolu sorunlarını önlemek için)
        if len(text) > 50:
            text = text[:50]
            # Son kelimeyi tam bırakmak için son alt çizgiyi bul
            last_underscore = text.rfind("_")
            if last_underscore > 20:  # Çok kısa olmamak için
                text = text[:last_underscore]

        return text
