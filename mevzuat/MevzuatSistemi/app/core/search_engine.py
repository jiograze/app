"""
Arama motoru - FTS ve semantik arama kombinasyonu
"""

import time
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import numpy as np
    print("numpy imported successfully")
    from sentence_transformers import SentenceTransformer
    print("sentence_transformers imported successfully")
    import faiss
    print("faiss imported successfully")
    EMBEDDING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML modules not available: {e}")
    EMBEDDING_AVAILABLE = False
except Exception as e:
    print(f"Error loading ML modules: {e}")
    EMBEDDING_AVAILABLE = False

from ..utils.logger import TimedOperation, log_performance_metric
from .text_analyzer import TurkishTextAnalyzer, EnhancedFTSQueryBuilder
from .semantic_search_alternative import SimpleTfIdfSemanticSearch

@dataclass
class SearchResult:
    """Arama sonucu veri yapısı"""
    id: int
    document_id: int
    article_number: str
    title: str
    content: str
    document_title: str
    law_number: str
    document_type: str
    is_repealed: bool
    is_amended: bool
    score: float
    match_type: str  # 'keyword', 'semantic', 'mixed'
    highlights: List[str] = None

class SearchEngine:
    """Hibrit arama motoru - FTS + Semantik arama"""
    
    def __init__(self, config_manager, database_manager):
        self.config = config_manager
        self.db = database_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Arama ayarları
        self.semantic_enabled = config_manager.get('search.semantic_enabled', True)
        self.max_results = config_manager.get('search.max_results', 20)
        self.semantic_weight = config_manager.get('search.semantic_weight', 0.4)
        self.keyword_weight = config_manager.get('search.keyword_weight', 0.6)
        
        # Embedding modeli ve indeks
        self.embedding_model: Optional[SentenceTransformer] = None
        self.faiss_index: Optional[faiss.Index] = None
        self.article_id_map: Dict[int, int] = {}  # FAISS index -> article_id
        
        # Arama önbelleği
        self.search_cache: Dict[str, List[SearchResult]] = {}
        
        # Cache
        self.search_cache = {}
        self.cache_size = config_manager.get('search.cache_size', 100)
        
        # Performans ayarları
        self.use_threading = config_manager.get('performance.threading.use_process_pool', False)
        self.max_workers = config_manager.get('performance.threading.max_worker_threads', 2)
        
        # Metin analiz sistemi
        self.text_analyzer = TurkishTextAnalyzer()
        self.query_builder = EnhancedFTSQueryBuilder(self.text_analyzer)
        
        # Alternatif semantik arama (TF-IDF tabanlı)
        self.tfidf_search = SimpleTfIdfSemanticSearch(config_manager)
        self.use_tfidf_fallback = True  # Sentence transformers yerine TF-IDF kullan
        
        self._initialize_embedding()
    
    def _initialize_embedding(self):
        """Embedding sistemini başlat"""
        if not self.semantic_enabled:
            self.logger.info("Semantik arama devre dışı")
            return
        
        # Önce Sentence Transformers'ı dene
        if EMBEDDING_AVAILABLE and not self.use_tfidf_fallback:
            try:
                with TimedOperation("embedding_model_load"):
                    model_name = self.config.get('embedding.model_name', 'sentence-transformers/all-MiniLM-L6-v2')
                    self.embedding_model = SentenceTransformer(model_name)
                    self.logger.info(f"Embedding modeli yüklendi: {model_name}")
                
                # FAISS indeksini yükle
                self._load_faiss_index()
                return
                
            except Exception as e:
                self.logger.error(f"Sentence Transformers hatası: {e}")
                self.logger.info("TF-IDF fallback kullanılacak")
                self.use_tfidf_fallback = True
        
        # TF-IDF fallback
        if self.use_tfidf_fallback:
            try:
                # Mevcut dokümanları al
                cursor = self.db.connection.cursor()
                cursor.execute("""
                    SELECT id, content_clean, content 
                    FROM articles 
                    WHERE content IS NOT NULL 
                    AND LENGTH(TRIM(COALESCE(content_clean, content))) > 50
                """)
                documents = []
                for row in cursor.fetchall():
                    documents.append({
                        'id': row[0],
                        'content_clean': row[1] or row[2],
                        'content': row[2]
                    })
                cursor.close()
                
                # TF-IDF modelini başlat
                if self.tfidf_search.initialize(documents):
                    self.logger.info(f"TF-IDF semantik arama başlatıldı: {len(documents)} dokuman")
                else:
                    self.logger.warning("TF-IDF semantik arama başlatılamadı")
                    self.semantic_enabled = False
                    
            except Exception as e:
                self.logger.error(f"TF-IDF başlatma hatası: {e}")
                self.semantic_enabled = False
    
    def _load_faiss_index(self):
        """FAISS indeksini diskten yükle"""
        try:
            index_folder = self.config.get_base_folder() / 'index'
            index_path = index_folder / 'faiss.index'
            map_path = index_folder / 'emb_map.json'
            
            if index_path.exists() and map_path.exists():
                # FAISS indeksini yükle
                self.faiss_index = faiss.read_index(str(index_path))
                
                # Article ID mapping'i yükle
                import json
                with open(map_path, 'r', encoding='utf-8') as f:
                    self.article_id_map = {int(k): v for k, v in json.load(f).items()}
                
                self.logger.info(f"FAISS indeksi yüklendi: {self.faiss_index.ntotal} vektör")
            else:
                # Yeni indeks oluştur
                self._create_empty_index()
                
        except Exception as e:
            self.logger.error(f"FAISS indeks yükleme hatası: {e}")
            self._create_empty_index()
    
    def _create_empty_index(self):
        """Boş FAISS indeksi oluştur"""
        if self.embedding_model:
            # Model boyutunu al
            sample_embedding = self.embedding_model.encode(["test"])
            dimension = sample_embedding.shape[1]
            
            # Flat indeks oluştur (basit ama etkili)
            self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner Product
            self.article_id_map = {}
            
            self.logger.info(f"Boş FAISS indeksi oluşturuldu: {dimension} boyut")
    
    def search(self, query: str, document_types: List[str] = None, 
              search_type: str = 'mixed', include_repealed: bool = False) -> List[SearchResult]:
        """
        Ana arama fonksiyonu
        
        Args:
            query: Arama sorgusu
            document_types: Filtrelenecek belge türleri ['KANUN', 'TÜZÜK', ...]
            search_type: 'keyword', 'semantic', 'mixed'
            include_repealed: Mülga maddeleri dahil et
            
        Returns:
            Arama sonuçları listesi
        """
        start_time = time.time()
        
        try:
            # Cache kontrolü
            cache_key = self._generate_cache_key(query, document_types, search_type, include_repealed)
            if cache_key in self.search_cache:
                cached_results = self.search_cache[cache_key]
                log_performance_metric("search_cache_hit", 0, {"query": query[:50]})
                return cached_results
            
            results = []
            
            # Arama türüne göre işlem
            if search_type == 'keyword':
                results = self._keyword_search(query, document_types, include_repealed)
            elif search_type == 'semantic' and self.semantic_enabled:
                results = self._semantic_search(query, document_types, include_repealed)
            elif search_type == 'mixed':
                results = self._mixed_search(query, document_types, include_repealed)
            else:
                # Fallback: keyword search
                results = self._keyword_search(query, document_types, include_repealed)
            
            # Sonuçları skoruna göre sırala
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Limit uygula
            results = results[:self.max_results]
            
            # Cache'e ekle
            self._add_to_cache(cache_key, results)
            
            # Arama geçmişine ekle
            execution_time = (time.time() - start_time) * 1000
            self.db.add_search_to_history(query, search_type, len(results), execution_time)
            
            # Performance log
            log_performance_metric("search_total", execution_time, {
                "query": query[:50],
                "type": search_type,
                "results": len(results)
            })
            
            self.logger.info(f"Arama tamamlandı: '{query}' -> {len(results)} sonuç ({execution_time:.1f}ms)")
            return results
            
        except Exception as e:
            self.logger.error(f"Arama hatası: {e}")
            return []
    
    def _keyword_search(self, query: str, document_types: List[str] = None, 
                       include_repealed: bool = False) -> List[SearchResult]:
        """FTS ile anahtar kelime araması"""
        
        with TimedOperation("keyword_search", details={"query": query[:50]}):
            # FTS sorgusu hazırla
            fts_query = self._prepare_fts_query(query)
            
            results = self.db.search_articles(
                fts_query, 
                document_types, 
                limit=self.max_results * 2  # Daha fazla al, sonra filtrele
            )
            
            search_results = []
            for result in results:
                # Mülga filtresi
                if not include_repealed and result.get('is_repealed'):
                    continue
                
                # Highlight oluştur
                highlights = self._generate_highlights(result['content'], query)
                
                search_result = SearchResult(
                    id=result['id'],
                    document_id=result['document_id'],
                    article_number=result['article_number'] or '',
                    title=result['title'] or '',
                    content=result['content'],
                    document_title=result['document_title'],
                    law_number=result['law_number'] or '',
                    document_type=result['document_type'],
                    is_repealed=result['is_repealed'],
                    is_amended=result['is_amended'],
                    score=result.get('rank', 1.0),  # FTS rank score
                    match_type='keyword',
                    highlights=highlights
                )
                
                search_results.append(search_result)
            
            return search_results
    
    def _semantic_search(self, query: str, document_types: List[str] = None,
                        include_repealed: bool = False) -> List[SearchResult]:
        """Semantik arama (FAISS veya TF-IDF)"""
        
        if not self.semantic_enabled:
            return []
        
        with TimedOperation("semantic_search", details={"query": query[:50]}):
            search_results = []
            
            # TF-IDF tabanlı semantik arama
            if self.use_tfidf_fallback:
                try:
                    tfidf_results = self.tfidf_search.search(query, top_k=self.max_results * 2)
                    
                    for article_id, score in tfidf_results:
                        # Veritabanından article bilgilerini al
                        article_data = self._get_article_with_document(article_id)
                        if not article_data:
                            continue
                        
                        # Filtreler
                        if document_types and article_data['document_type'] not in document_types:
                            continue
                        
                        if not include_repealed and article_data.get('is_repealed'):
                            continue
                        
                        # Semantik highlight
                        highlights = self._generate_semantic_highlights(article_data['content'], query)
                        
                        search_result = SearchResult(
                            id=article_data['id'],
                            document_id=article_data['document_id'],
                            article_number=article_data['article_number'] or '',
                            title=article_data['title'] or '',
                            content=article_data['content'],
                            document_title=article_data['document_title'],
                            law_number=article_data['law_number'] or '',
                            document_type=article_data['document_type'],
                            is_repealed=article_data['is_repealed'],
                            is_amended=article_data['is_amended'],
                            score=float(score),  # TF-IDF similarity
                            match_type='semantic',
                            highlights=highlights
                        )
                        
                        search_results.append(search_result)
                    
                    return search_results
                    
                except Exception as e:
                    self.logger.error(f"TF-IDF arama hatası: {e}")
                    return []
            
            # FAISS tabanlı semantik arama (fallback)
            elif self.embedding_model and self.faiss_index:
                try:
                    # Query embedding oluştur
                    query_embedding = self.embedding_model.encode([query])
                    
                    # FAISS ile benzer vektörleri bul
                    k = min(self.max_results * 3, self.faiss_index.ntotal)
                    if k == 0:
                        return []
                    
                    scores, indices = self.faiss_index.search(query_embedding, k)
                    
                    for score, idx in zip(scores[0], indices[0]):
                        if idx == -1:  # FAISS invalid index
                            continue
                        
                        # Article ID'yi al
                        article_id = self.article_id_map.get(idx)
                        if not article_id:
                            continue
                        
                        # Veritabanından article bilgilerini al
                        article_data = self._get_article_with_document(article_id)
                        if not article_data:
                            continue
                        
                        # Filtreler
                        if document_types and article_data['document_type'] not in document_types:
                            continue
                        
                        if not include_repealed and article_data.get('is_repealed'):
                            continue
                        
                        # Semantik highlight
                        highlights = self._generate_semantic_highlights(article_data['content'], query)
                        
                        search_result = SearchResult(
                            id=article_data['id'],
                            document_id=article_data['document_id'],
                            article_number=article_data['article_number'] or '',
                            title=article_data['title'] or '',
                            content=article_data['content'],
                            document_title=article_data['document_title'],
                            law_number=article_data['law_number'] or '',
                            document_type=article_data['document_type'],
                            is_repealed=article_data['is_repealed'],
                            is_amended=article_data['is_amended'],
                            score=float(score),  # Cosine similarity
                            match_type='semantic',
                            highlights=highlights
                        )
                        
                        search_results.append(search_result)
                    
                    return search_results
                    
                except Exception as e:
                    self.logger.error(f"FAISS arama hatası: {e}")
                    return []
            
            return []
    
    def _mixed_search(self, query: str, document_types: List[str] = None,
                     include_repealed: bool = False) -> List[SearchResult]:
        """Karma arama - FTS + Semantik"""
        
        if self.use_threading:
            return self._mixed_search_threaded(query, document_types, include_repealed)
        else:
            return self._mixed_search_sequential(query, document_types, include_repealed)
    
    def _mixed_search_sequential(self, query: str, document_types: List[str] = None,
                                include_repealed: bool = False) -> List[SearchResult]:
        """Sıralı karma arama"""
        
        # Her iki arama türünü çalıştır
        keyword_results = self._keyword_search(query, document_types, include_repealed)
        semantic_results = self._semantic_search(query, document_types, include_repealed)
        
        # Sonuçları birleştir ve skorları normalize et
        return self._combine_search_results(keyword_results, semantic_results)
    
    def _mixed_search_threaded(self, query: str, document_types: List[str] = None,
                              include_repealed: bool = False) -> List[SearchResult]:
        """Threading ile karma arama"""
        
        keyword_results = []
        semantic_results = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Her iki arama türünü paralel başlat
            future_keyword = executor.submit(self._keyword_search, query, document_types, include_repealed)
            future_semantic = executor.submit(self._semantic_search, query, document_types, include_repealed)
            
            # Sonuçları topla
            for future in as_completed([future_keyword, future_semantic]):
                try:
                    if future == future_keyword:
                        keyword_results = future.result()
                    else:
                        semantic_results = future.result()
                except Exception as e:
                    self.logger.error(f"Threading arama hatası: {e}")
        
        return self._combine_search_results(keyword_results, semantic_results)
    
    def _combine_search_results(self, keyword_results: List[SearchResult], 
                               semantic_results: List[SearchResult]) -> List[SearchResult]:
        """Arama sonuçlarını birleştir ve skorla"""
        
        # ID bazlı mapping
        combined = {}
        
        # Keyword sonuçları
        for result in keyword_results:
            result.score = result.score * self.keyword_weight
            combined[result.id] = result
        
        # Semantic sonuçları
        for result in semantic_results:
            if result.id in combined:
                # Zaten var - skorları birleştir
                existing = combined[result.id]
                existing.score += result.score * self.semantic_weight
                existing.match_type = 'mixed'
                # Highlight'ları birleştir
                if result.highlights:
                    existing.highlights.extend(result.highlights)
            else:
                # Yeni sonuç
                result.score = result.score * self.semantic_weight
                combined[result.id] = result
        
        return list(combined.values())
    
    def _prepare_fts_query(self, query: str) -> str:
        """FTS5 için gelişmiş sorgu hazırla"""
        try:
            # Yeni query builder kullan
            return self.query_builder.build_query(query, 'comprehensive')
        except Exception as e:
            self.logger.error(f"FTS sorgu hazırlama hatası: {e}")
            # Fallback - basit sorgu
            words = query.strip().split()
            if len(words) == 1:
                return f'"{words[0]}"*'
            else:
                return ' AND '.join(f'"{word}"*' for word in words if len(word) > 2)
    
    def _generate_highlights(self, content: str, query: str, max_highlights: int = 3) -> List[str]:
        """Gelişmiş anahtar kelime highlight'ları oluştur"""
        try:
            highlights = []
            
            # Metin analizi ile alternatif arama terimleri oluştur
            search_terms = self.text_analyzer.create_search_terms(query)
            
            import re
            content_lower = content.lower()
            
            for term in search_terms:
                words = term.split()
                
                for word in words:
                    if len(word) < 3:
                        continue
                    
                    # Hem orijinal hem normalize edilmiş kelimeyi ara
                    patterns = [
                        rf'\b\w*{re.escape(word)}\w*\b',
                        rf'\b\w*{re.escape(self.text_analyzer._normalize_text(word))}\w*\b'
                    ]
                    
                    for pattern in patterns:
                        matches = list(re.finditer(pattern, content, re.IGNORECASE))
                        
                        for match in matches:
                            start = max(0, match.start() - 60)
                            end = min(len(content), match.end() + 60)
                            snippet = content[start:end]
                            
                            # Highlight ekle
                            highlighted = re.sub(
                                pattern, 
                                rf'<mark>\g<0></mark>', 
                                snippet, 
                                flags=re.IGNORECASE
                            )
                            
                            if highlighted.strip() not in highlights:
                                highlights.append(highlighted.strip())
                            
                            if len(highlights) >= max_highlights:
                                break
                    
                    if len(highlights) >= max_highlights:
                        break
                
                if len(highlights) >= max_highlights:
                    break
            
            return highlights[:max_highlights]
            
        except Exception as e:
            self.logger.error(f"Highlight oluşturma hatası: {e}")
            # Fallback - basit highlight
            import re
            highlights = []
            words = query.lower().split()
            
            for word in words:
                if len(word) >= 3:
                    pattern = rf'\b\w*{re.escape(word)}\w*\b'
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    
                    for match in matches:
                        start = max(0, match.start() - 50)
                        end = min(len(content), match.end() + 50)
                        snippet = content[start:end]
                        highlighted = re.sub(pattern, rf'<mark>\g<0></mark>', snippet, flags=re.IGNORECASE)
                        highlights.append(highlighted.strip())
                        
                        if len(highlights) >= max_highlights:
                            break
            
            return highlights[:max_highlights]
    
    def _generate_semantic_highlights(self, content: str, query: str, max_highlights: int = 2) -> List[str]:
        """Semantik highlight'lar (basit sentence-based)"""
        sentences = content.split('.')
        highlights = []
        
        # İlk birkaç cümleyi al (basit yaklaşım)
        for sentence in sentences[:max_highlights]:
            if len(sentence.strip()) > 20:
                highlights.append(sentence.strip() + '.')
        
        return highlights
    
    def _get_article_with_document(self, article_id: int) -> Optional[Dict]:
        """Article'ı document bilgileriyle birlikte getir"""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT 
                a.id, a.document_id, a.article_number, a.title, a.content,
                a.is_repealed, a.is_amended,
                d.title as document_title, d.law_number, d.document_type
            FROM articles a
            JOIN documents d ON a.document_id = d.id
            WHERE a.id = ?
        """, (article_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def _generate_cache_key(self, query: str, document_types: List[str], 
                           search_type: str, include_repealed: bool) -> str:
        """Cache anahtarı oluştur"""
        import hashlib
        
        key_data = f"{query}_{document_types}_{search_type}_{include_repealed}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _add_to_cache(self, key: str, results: List[SearchResult]):
        """Sonuçları cache'e ekle"""
        if len(self.search_cache) >= self.cache_size:
            # En eski öğeyi sil (basit FIFO)
            oldest_key = next(iter(self.search_cache))
            del self.search_cache[oldest_key]
        
        self.search_cache[key] = results.copy()
    
    def add_article_to_index(self, article_id: int, content: str):
        """Yeni article'ı indekse ekle"""
        if not self.semantic_enabled or not self.embedding_model:
            return
        
        try:
            # Embedding oluştur
            embedding = self.embedding_model.encode([content])
            
            # FAISS'e ekle
            if self.faiss_index:
                self.faiss_index.add(embedding)
                
                # Mapping güncelle
                new_index = self.faiss_index.ntotal - 1
                self.article_id_map[new_index] = article_id
                
                self.logger.debug(f"Article {article_id} indekse eklendi")
            
        except Exception as e:
            self.logger.error(f"İndekse ekleme hatası: {e}")
    
    def rebuild_index(self):
        """Tüm indeksi yeniden oluştur"""
        if not self.semantic_enabled or not self.embedding_model:
            return False
        
        try:
            self.logger.info("FAISS indeksi yeniden oluşturuluyor...")
            
            # Tüm article'ları al
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT id, content_clean FROM articles WHERE content_clean IS NOT NULL")
            articles = cursor.fetchall()
            cursor.close()
            
            if not articles:
                self.logger.warning("İndekslenecek article bulunamadı")
                return False
            
            # Embeddings oluştur
            contents = [article[1] for article in articles]
            article_ids = [article[0] for article in articles]
            
            with TimedOperation("rebuild_embeddings", details={"count": len(contents)}):
                embeddings = self.embedding_model.encode(contents)
            
            # Yeni indeks oluştur
            dimension = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            
            # Embeddings'leri ekle
            self.faiss_index.add(embeddings)
            
            # Mapping oluştur
            self.article_id_map = {i: article_ids[i] for i in range(len(article_ids))}
            
            # Diske kaydet
            self._save_faiss_index()
            
            self.logger.info(f"FAISS indeksi yeniden oluşturuldu: {len(articles)} artikel")
            return True
            
        except Exception as e:
            self.logger.error(f"İndeks yeniden oluşturma hatası: {e}")
            return False
    
    def _save_faiss_index(self):
        """FAISS indeksini diske kaydet"""
        try:
            index_folder = self.config.get_base_folder() / 'index'
            index_folder.mkdir(parents=True, exist_ok=True)
            
            # FAISS indeksini kaydet
            index_path = index_folder / 'faiss.index'
            faiss.write_index(self.faiss_index, str(index_path))
            
            # Article mapping'i kaydet
            map_path = index_folder / 'emb_map.json'
            import json
            with open(map_path, 'w', encoding='utf-8') as f:
                json.dump(self.article_id_map, f, ensure_ascii=False, indent=2)
            
            self.logger.info("FAISS indeksi kaydedildi")
            
        except Exception as e:
            self.logger.error(f"FAISS kaydetme hatası: {e}")
    
    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Arama önerileri"""
        if len(partial_query) < 2:
            return []
        
        try:
            # Son aramalardan öneriler
            recent_searches = self.db.get_search_history(limit=50)
            
            suggestions = []
            for search in recent_searches:
                query = search['query']
                if partial_query.lower() in query.lower() and query not in suggestions:
                    suggestions.append(query)
                    
                    if len(suggestions) >= limit:
                        break
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Öneri oluşturma hatası: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Arama motoru istatistikleri"""
        return {
            'semantic_enabled': self.semantic_enabled,
            'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
            'cache_size': len(self.search_cache),
            'embedding_model': self.config.get('embedding.model_name') if self.embedding_model else None
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Performans istatistikleri"""
        try:
            cursor = self.db.connection.cursor()
            
            # Toplam arama sayısı
            cursor.execute("SELECT COUNT(*) FROM search_history")
            total_searches = cursor.fetchone()[0]
            
            # Ortalama arama süresi
            cursor.execute("""
                SELECT AVG(execution_time_ms), 
                       MIN(execution_time_ms), 
                       MAX(execution_time_ms)
                FROM search_history 
                WHERE execution_time_ms IS NOT NULL
            """)
            timing_stats = cursor.fetchone()
            
            # Arama türü dağılımı
            cursor.execute("""
                SELECT query_type, COUNT(*) 
                FROM search_history 
                GROUP BY query_type
            """)
            search_type_counts = dict(cursor.fetchall())
            
            cursor.close()
            
            return {
                'total_searches': total_searches,
                'average_execution_time_ms': timing_stats[0] if timing_stats[0] else 0,
                'min_execution_time_ms': timing_stats[1] if timing_stats[1] else 0,
                'max_execution_time_ms': timing_stats[2] if timing_stats[2] else 0,
                'search_type_counts': search_type_counts,
                'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
                'semantic_enabled': self.semantic_enabled,
                'cache_size': len(self.search_cache) if hasattr(self, 'search_cache') else 0
            }
            
        except Exception as e:
            self.logger.error(f"Performans istatistikleri alınamadı: {e}")
            return {
                'total_searches': 0,
                'average_execution_time_ms': 0,
                'min_execution_time_ms': 0,
                'max_execution_time_ms': 0,
                'search_type_counts': {},
                'faiss_index_size': 0,
                'semantic_enabled': self.semantic_enabled,
                'cache_size': 0
            }
    
    def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """Arama önerileri al"""
        try:
            if len(query.strip()) < 2:
                return []
            
            cursor = self.db.connection.cursor()
            
            # Son aramalardan önerileri al
            cursor.execute("""
                SELECT DISTINCT query_text
                FROM search_history 
                WHERE query_text LIKE ? 
                ORDER BY search_date DESC 
                LIMIT ?
            """, (f"%{query}%", limit))
            
            suggestions = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            # Eğer yeterli öneri yoksa, popüler terimlerden ekle
            if len(suggestions) < limit:
                popular_terms = [
                    "vergi kanunu", "türk ceza kanunu", "medeni kanun", 
                    "borçlar kanunu", "iş kanunu", "sosyal güvenlik",
                    "ticaret kanunu", "çevre kanunu", "eğitim", "sağlık"
                ]
                
                query_lower = query.lower()
                for term in popular_terms:
                    if query_lower in term and term not in suggestions:
                        suggestions.append(term)
                        if len(suggestions) >= limit:
                            break
            
            return suggestions[:limit]
            
        except Exception as e:
            self.logger.error(f"Öneri alma hatası: {e}")
            return []
    
    def rebuild_index(self) -> bool:
        """Semantik indeksi yeniden oluştur"""
        try:
            self.logger.info("Semantik indeks yeniden oluşturuluyor...")
            
            # Mevcut indeksi temizle
            self.faiss_index = None
            self.embedding_id_map = {}
            
            if not self.semantic_enabled:
                self.logger.warning("Semantik arama devre dışı, indeks oluşturulmadı")
                return True
            
            # Tüm belgeleri al
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT article_id, content 
                FROM articles 
                WHERE content IS NOT NULL 
                AND LENGTH(TRIM(content)) > 50
            """)
            
            articles = cursor.fetchall()
            cursor.close()
            
            if not articles:
                self.logger.warning("İndekslenecek makale bulunamadı")
                return True
            
            # Embeddings oluştur
            contents = [article[1] for article in articles]
            article_ids = [article[0] for article in articles]
            
            # Batch halinde embedding'ler oluştur
            batch_size = 32
            all_embeddings = []
            
            for i in range(0, len(contents), batch_size):
                batch_contents = contents[i:i+batch_size]
                batch_embeddings = self.model.encode(batch_contents)
                all_embeddings.extend(batch_embeddings)
            
            # FAISS indeksi oluştur
            import numpy as np
            embeddings_array = np.array(all_embeddings).astype('float32')
            
            import faiss
            dimension = embeddings_array.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            self.faiss_index.add(embeddings_array)
            
            # ID mapping oluştur
            self.embedding_id_map = {i: article_ids[i] for i in range(len(article_ids))}
            
            self.logger.info(f"Semantik indeks oluşturuldu: {len(articles)} makale indekslendi")
            return True
            
        except Exception as e:
            self.logger.error(f"İndeks yeniden oluşturma hatası: {e}")
            return False
