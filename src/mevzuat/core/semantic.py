"""
Sentence Transformers alternatifi - Basit TF-IDF tabanlı semantik arama
"""

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimpleTfIdfSemanticSearch:
    """TF-IDF tabanlı basit semantik arama"""

    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)

        # TF-IDF parametreleri
        self.max_features = 10000
        self.min_df = 2
        self.max_df = 0.8
        self.ngram_range = (1, 2)  # Unigram ve bigram

        # Model ve vektörler
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.document_vectors: Optional[np.ndarray] = None
        self.document_ids: List[int] = []

        # Cache dosyaları
        self.model_folder = config_manager.get_base_folder() / "tfidf_model"
        self.model_folder.mkdir(parents=True, exist_ok=True)

        self.vectorizer_path = self.model_folder / "tfidf_vectorizer.pkl"
        self.vectors_path = self.model_folder / "document_vectors.npy"
        self.ids_path = self.model_folder / "document_ids.pkl"

    def initialize(self, documents: List[Dict[str, Any]] = None):
        """Model başlatma"""
        try:
            if self._load_from_cache():
                self.logger.info("TF-IDF modeli cache'den yüklendi")
                return True

            if documents:
                self._train_model(documents)
                return True
            else:
                self.logger.warning("Dokuman listesi verilmedi, model başlatılamadı")
                return False

        except Exception as e:
            self.logger.error(f"TF-IDF model başlatma hatası: {e}")
            return False

    def _load_from_cache(self) -> bool:
        """Cache'den modeli yükle"""
        try:
            if (
                self.vectorizer_path.exists()
                and self.vectors_path.exists()
                and self.ids_path.exists()
            ):

                # Vectorizer yükle
                with open(self.vectorizer_path, "rb") as f:
                    self.vectorizer = pickle.load(f)

                # Vektörler yükle
                self.document_vectors = np.load(self.vectors_path)

                # Document ID'ler yükle
                with open(self.ids_path, "rb") as f:
                    self.document_ids = pickle.load(f)

                self.logger.info(
                    f"TF-IDF modeli yüklendi: {len(self.document_ids)} dokuman"
                )
                return True

            return False

        except Exception as e:
            self.logger.error(f"Cache yükleme hatası: {e}")
            return False

    def _save_to_cache(self):
        """Modeli cache'e kaydet"""
        try:
            # Vectorizer kaydet
            with open(self.vectorizer_path, "wb") as f:
                pickle.dump(self.vectorizer, f)

            # Vektörler kaydet
            np.save(self.vectors_path, self.document_vectors)

            # Document ID'ler kaydet
            with open(self.ids_path, "wb") as f:
                pickle.dump(self.document_ids, f)

            self.logger.info("TF-IDF modeli cache'e kaydedildi")

        except Exception as e:
            self.logger.error(f"Cache kaydetme hatası: {e}")

    def _train_model(self, documents: List[Dict[str, Any]]):
        """Model eğitimi"""
        try:
            self.logger.info(f"TF-IDF modeli eğitiliyor: {len(documents)} dokuman")

            # Metin içeriklerini hazırla
            texts = []
            doc_ids = []

            for doc in documents:
                content = doc.get("content_clean", "") or doc.get("content", "")
                if content and len(content.strip()) > 10:
                    texts.append(content)
                    doc_ids.append(doc["id"])

            if not texts:
                raise ValueError("Geçerli metin içeriği bulunamadı")

            # TF-IDF vectorizer oluştur
            self.vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                min_df=self.min_df,
                max_df=self.max_df,
                ngram_range=self.ngram_range,
                stop_words=None,  # Türkçe stop words listesi eklenebilir
                lowercase=True,
                token_pattern=r"\b[a-zA-ZçğıöşüÇĞIÖŞÜ]{2,}\b",  # Türkçe karakterler dahil
            )

            # Vektörleri oluştur
            self.document_vectors = self.vectorizer.fit_transform(texts)
            self.document_ids = doc_ids

            # Cache'e kaydet
            self._save_to_cache()

            self.logger.info(
                f"TF-IDF modeli eğitildi: {len(texts)} dokuman, {self.document_vectors.shape[1]} özellik"
            )

        except Exception as e:
            self.logger.error(f"Model eğitim hatası: {e}")
            raise

    def search(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """Semantik arama yap"""
        try:
            if not self.vectorizer or self.document_vectors is None:
                self.logger.warning("Model henüz yüklenmedi")
                return []

            # Query vektörü oluştur
            query_vector = self.vectorizer.transform([query])

            # Cosine similarity hesapla
            similarities = cosine_similarity(
                query_vector, self.document_vectors
            ).flatten()

            # Sonuçları sırala
            top_indices = np.argsort(similarities)[::-1][:top_k]

            results = []
            for idx in top_indices:
                if similarities[idx] > 0.01:  # Minimum threshold
                    doc_id = self.document_ids[idx]
                    score = float(similarities[idx])
                    results.append((doc_id, score))

            self.logger.debug(f"TF-IDF arama: '{query}' -> {len(results)} sonuç")
            return results

        except Exception as e:
            self.logger.error(f"TF-IDF arama hatası: {e}")
            return []

    def add_document(self, doc_id: int, content: str):
        """Yeni dokuman ekle"""
        try:
            if not self.vectorizer:
                self.logger.warning("Model henüz yüklenmedi, dokuman eklenemedi")
                return

            # Yeni dokümanı vektörleştir
            new_vector = self.vectorizer.transform([content])

            # Mevcut vektörlere ekle
            if self.document_vectors is not None:
                self.document_vectors = np.vstack([self.document_vectors, new_vector])
            else:
                self.document_vectors = new_vector

            self.document_ids.append(doc_id)

            # Cache güncelle
            self._save_to_cache()

            self.logger.debug(f"Dokuman eklendi: {doc_id}")

        except Exception as e:
            self.logger.error(f"Dokuman ekleme hatası: {e}")

    def rebuild_index(self, documents: List[Dict[str, Any]]):
        """İndeksi yeniden oluştur"""
        try:
            self.logger.info("TF-IDF indeksi yeniden oluşturuluyor...")

            # Önce cache temizle
            self._clear_cache()

            # Modeli yeniden eğit
            self._train_model(documents)

            self.logger.info("TF-IDF indeksi yeniden oluşturuldu")
            return True

        except Exception as e:
            self.logger.error(f"İndeks yeniden oluşturma hatası: {e}")
            return False

    def _clear_cache(self):
        """Cache dosyalarını temizle"""
        try:
            for path in [self.vectorizer_path, self.vectors_path, self.ids_path]:
                if path.exists():
                    path.unlink()
        except Exception as e:
            self.logger.error(f"Cache temizleme hatası: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Model istatistikleri"""
        return {
            "model_loaded": self.vectorizer is not None,
            "document_count": len(self.document_ids) if self.document_ids else 0,
            "feature_count": (
                self.document_vectors.shape[1]
                if self.document_vectors is not None
                else 0
            ),
            "max_features": self.max_features,
            "ngram_range": self.ngram_range,
        }
