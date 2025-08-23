"""
Veritabanı yöneticisi - SQLite tabloları ve işlemleri
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime

class DatabaseManager:
    """SQLite veritabanı yönetim sınıfı"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db_path = config_manager.get_db_path()
        self.connection: Optional[sqlite3.Connection] = None
        
        # Performans ayarları
        self.journal_mode = config_manager.get('performance.sqlite_journal_mode', 'WAL')
        self.cache_size_mb = config_manager.get('performance.sqlite_cache_size_mb', 64)
    
    def initialize(self):
        """Veritabanını başlat ve tabloları oluştur"""
        try:
            # DB klasörünü oluştur
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Bağlantıyı kur
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            
            # Performans ayarları
            self._configure_database()
            
            # Tabloları oluştur
            self._create_tables()
            
            # İndeksleri oluştur
            self._create_indexes()
            
            self.logger.info(f"Veritabanı başlatıldı: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Veritabanı başlatma hatası: {e}")
            raise
    
    def _configure_database(self):
        """Veritabanı performans ayarları"""
        cursor = self.connection.cursor()
        
        # Journal modu
        cursor.execute(f"PRAGMA journal_mode={self.journal_mode}")
        
        # Cache boyutu (sayfa sayısı olarak, her sayfa ~1KB)
        cache_pages = self.cache_size_mb * 1024
        cursor.execute(f"PRAGMA cache_size={cache_pages}")
        
        # Foreign key kontrolü
        cursor.execute("PRAGMA foreign_keys=ON")
        
        # Temp store bellek kullanımı
        cursor.execute("PRAGMA temp_store=MEMORY")
        
        # Synchronous mod (performans için)
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        cursor.close()
        self.connection.commit()
    
    def _create_tables(self):
        """Tüm tabloları oluştur"""
        
        # Belgeler tablosu
        documents_table = """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            law_number TEXT,
            document_type TEXT NOT NULL,
            category TEXT,
            subcategory TEXT,
            original_filename TEXT,
            stored_filename TEXT,
            file_path TEXT NOT NULL,
            file_hash TEXT UNIQUE,  -- Unique constraint eklendi
            file_size INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            effective_date TEXT,
            publication_date TEXT,
            status TEXT DEFAULT 'ACTIVE',
            version_number INTEGER DEFAULT 1,
            parent_document_id INTEGER REFERENCES documents(id),
            metadata TEXT -- JSON formatında ek bilgiler
        )
        """
        
        # Maddeler tablosu
        articles_table = """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            article_number TEXT,
            title TEXT,
            content TEXT NOT NULL,
            content_clean TEXT, -- Temizlenmiş metin (arama için)
            seq_index INTEGER, -- Belgede sıralama
            is_repealed BOOLEAN DEFAULT FALSE,
            is_amended BOOLEAN DEFAULT FALSE,
            amendment_info TEXT, -- Değişiklik bilgisi
            article_type TEXT DEFAULT 'MADDE', -- MADDE, FIKRA, BEND, vb.
            parent_article_id INTEGER REFERENCES articles(id),
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
        """
        
        # Kullanıcı kategorileri
        user_categories_table = """
        CREATE TABLE IF NOT EXISTS user_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#808080',
            description TEXT,
            parent_id INTEGER REFERENCES user_categories(id),
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
        """
        
        # Kullanıcı notları
        user_notes_table = """
        CREATE TABLE IF NOT EXISTS user_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            title TEXT,
            content TEXT NOT NULL,
            note_type TEXT DEFAULT 'USER', -- USER, SYSTEM, AUTO
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
        """
        
        # Madde-kategori ilişkileri
        article_categories_table = """
        CREATE TABLE IF NOT EXISTS article_categories (
            article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES user_categories(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            PRIMARY KEY (article_id, category_id)
        )
        """
        
        # Madde ilişkileri
        article_relations_table = """
        CREATE TABLE IF NOT EXISTS article_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            target_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
            relation_type TEXT NOT NULL, -- REFERENCE, AMENDMENT, REPEAL, RELATED
            confidence REAL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            UNIQUE(source_id, target_id, relation_type)
        )
        """
        
        # Arama geçmişi
        search_history_table = """
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            query_type TEXT DEFAULT 'MIXED', -- KEYWORD, SEMANTIC, MIXED
            results_count INTEGER DEFAULT 0,
            execution_time_ms REAL,
            created_at TEXT NOT NULL
        )
        """
        
        # Favoriler
        favorites_table = """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            title TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
        
        # İşlem geçmişi (undo için)
        operations_table = """
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL, -- INSERT, UPDATE, DELETE, MOVE
            table_name TEXT NOT NULL,
            record_id INTEGER,
            old_values TEXT, -- JSON formatında eski değerler
            new_values TEXT, -- JSON formatında yeni değerler
            description TEXT,
            can_undo BOOLEAN DEFAULT TRUE,
            created_at TEXT NOT NULL
        )
        """
        
        # FTS tablosu (Full Text Search)
        fts_table = """
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            title, 
            content, 
            content_clean, 
            article_number,
            content=articles,
            content_rowid=id
        )
        """
        
        # Tablolar listesi
        tables = [
            documents_table,
            articles_table,
            user_categories_table,
            user_notes_table,
            article_categories_table,
            article_relations_table,
            search_history_table,
            favorites_table,
            operations_table,
            fts_table
        ]
        
        cursor = self.connection.cursor()
        
        for table in tables:
            cursor.execute(table)
            
        cursor.close()
        self.connection.commit()
        
        self.logger.info("Tüm tablolar oluşturuldu")
    
    def _create_indexes(self):
        """Performans indekslerini oluştur"""
        indexes = [
            # Belgeler indeksleri
            "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type)",
            "CREATE INDEX IF NOT EXISTS idx_documents_law_number ON documents(law_number)",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash)",
            
            # Maddeler indeksleri
            "CREATE INDEX IF NOT EXISTS idx_articles_document_id ON articles(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_articles_number ON articles(article_number)",
            "CREATE INDEX IF NOT EXISTS idx_articles_seq_index ON articles(seq_index)",
            "CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(is_repealed, is_amended)",
            "CREATE INDEX IF NOT EXISTS idx_articles_type ON articles(article_type)",
            
            # İlişkiler indeksleri
            "CREATE INDEX IF NOT EXISTS idx_article_relations_source ON article_relations(source_id)",
            "CREATE INDEX IF NOT EXISTS idx_article_relations_target ON article_relations(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_article_relations_type ON article_relations(relation_type)",
            
            # Notlar indeksleri
            "CREATE INDEX IF NOT EXISTS idx_user_notes_article ON user_notes(article_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_notes_document ON user_notes(document_id)",
            
            # Arama geçmişi indeksi
            "CREATE INDEX IF NOT EXISTS idx_search_history_created ON search_history(created_at)",
            
            # Operasyonlar indeksi
            "CREATE INDEX IF NOT EXISTS idx_operations_created ON operations(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_operations_table_record ON operations(table_name, record_id)"
        ]
        
        cursor = self.connection.cursor()
        
        for index in indexes:
            cursor.execute(index)
        
        cursor.close()
        self.connection.commit()
        
        self.logger.info("Tüm indeksler oluşturuldu")
    
    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()
    
    def insert_document(self, document_data: Dict[str, Any]) -> int:
        """Yeni belge ekle"""
        required_fields = ['title', 'document_type', 'file_path']
        for field in required_fields:
            if field not in document_data:
                raise ValueError(f"Gerekli alan eksik: {field}")
        
        # Varsayılan değerler
        document_data.setdefault('created_at', datetime.now().isoformat())
        document_data.setdefault('status', 'ACTIVE')
        document_data.setdefault('version_number', 1)
        
        with self.transaction() as cursor:
            placeholders = ', '.join(['?' for _ in document_data])
            columns = ', '.join(document_data.keys())
            
            query = f"INSERT INTO documents ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(document_data.values()))
            
            doc_id = cursor.lastrowid
            self.logger.info(f"Belge eklendi: {doc_id}")
            return doc_id
    
    def insert_article(self, article_data: Dict[str, Any]) -> int:
        """Yeni madde ekle"""
        if 'document_id' not in article_data or 'content' not in article_data:
            raise ValueError("document_id ve content alanları gerekli")
        
        article_data.setdefault('created_at', datetime.now().isoformat())
        
        with self.transaction() as cursor:
            placeholders = ', '.join(['?' for _ in article_data])
            columns = ', '.join(article_data.keys())
            
            query = f"INSERT INTO articles ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(article_data.values()))
            
            article_id = cursor.lastrowid
            
            # FTS tablosuna da ekle
            if 'title' in article_data and 'content' in article_data:
                cursor.execute("""
                    INSERT INTO articles_fts (rowid, title, content, content_clean, article_number)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    article_id,
                    article_data.get('title', ''),
                    article_data.get('content', ''),
                    article_data.get('content_clean', ''),
                    article_data.get('article_number', '')
                ))
            
            self.logger.debug(f"Madde eklendi: {article_id}")
            return article_id
    
    def search_articles(self, query: str, document_types: List[str] = None, 
                       limit: int = 20) -> List[Dict[str, Any]]:
        """FTS ile madde arama"""
        
        base_query = """
        SELECT 
            a.id, a.document_id, a.article_number, a.title, a.content,
            a.is_repealed, a.is_amended,
            d.title as document_title, d.law_number, d.document_type,
            rank
        FROM articles_fts 
        JOIN articles a ON articles_fts.rowid = a.id
        JOIN documents d ON a.document_id = d.id
        WHERE articles_fts MATCH ?
        """
        
        params = [query]
        
        if document_types:
            placeholders = ', '.join(['?' for _ in document_types])
            base_query += f" AND d.document_type IN ({placeholders})"
            params.extend(document_types)
        
        base_query += " ORDER BY rank LIMIT ?"
        params.append(limit)
        
        cursor = self.connection.cursor()
        cursor.execute(base_query, params)
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        
        return results
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """ID ile belge getir"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def get_articles_by_document(self, doc_id: int) -> List[Dict[str, Any]]:
        """Belgeye ait maddeleri getir"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM articles 
            WHERE document_id = ? 
            ORDER BY seq_index, article_number
        """, (doc_id,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        return results
    
    def add_search_to_history(self, query: str, query_type: str, 
                            results_count: int, execution_time_ms: float):
        """Arama geçmişine ekle"""
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO search_history 
                (query, query_type, results_count, execution_time_ms, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (query, query_type, results_count, execution_time_ms, datetime.now().isoformat()))
    
    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Arama geçmişini getir"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM search_history 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        return results
    
    def close(self):
        """Veritabanı bağlantısını kapat"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Veritabanı bağlantısı kapatıldı")
    
    def vacuum(self):
        """Veritabanı bakımı (VACUUM)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("VACUUM")
            cursor.close()
            self.logger.info("Veritabanı VACUUM tamamlandı")
        except Exception as e:
            self.logger.error(f"VACUUM hatası: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Veritabanı istatistikleri"""
        cursor = self.connection.cursor()
        
        stats = {}
        
        # Tablo sayıları
        tables = ['documents', 'articles', 'user_notes', 'search_history', 'favorites']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]
        
        # Dosya boyutu
        if self.db_path.exists():
            stats['file_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
        
        cursor.close()
        return stats
    
    def __del__(self):
        """Nesne yok edilirken bağlantıyı kapat"""
        try:
            self.close()
        except:
            pass
