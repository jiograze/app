"""
Semantic Search test scriptı
"""

import os
import sys
from pathlib import Path

# Proje path'ini ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database_manager import DatabaseManager
from app.core.search_engine import HybridSearchEngine, SearchResult
from app.utils.config_manager import ConfigManager
from app.utils.logger import setup_logger


def test_semantic_search():
    """Semantic search'ü test et"""
    print("🔍 Semantic Search Test Edilyor...")

    # Logger ve config setup
    logger = setup_logger("SEMANTIC_TEST")
    config = ConfigManager(project_root / "config" / "config.yaml")

    # Database bağlantısı
    base_folder = config.get("base_folder", str(project_root / "test_data"))
    db = DatabaseManager(base_folder)

    print(f"📂 Database: {db.db_path}")
    print(f"📊 Database bağlantı durumu: {'✅ Aktif' if db.connection else '❌ Yok'}")

    # Search engine oluştur
    try:
        search_engine = HybridSearchEngine(db, config)
        print("✅ Search Engine oluşturuldu")

        # Semantic search durumu kontrol et
        semantic_config = config.get("search", {})
        print(f"📋 Semantic Arama Konfigürasyonu:")
        print(f"   - Aktif: {semantic_config.get('semantic_enabled', True)}")
        print(f"   - Max Sonuç: {semantic_config.get('max_results', 20)}")
        print(f"   - Semantic Weight: {semantic_config.get('semantic_weight', 0.4)}")
        print(f"   - Keyword Weight: {semantic_config.get('keyword_weight', 0.6)}")

        # Model durumu kontrol et
        print(f"\n🤖 Model Durumu:")
        print(
            f"   - Semantic Enabled: {'✅' if search_engine.semantic_enabled else '❌'}"
        )
        if hasattr(search_engine, "model") and search_engine.model:
            print(f"   - Model Yüklendi: ✅")
            print(f"   - Model Tipi: {type(search_engine.model).__name__}")
        else:
            print(f"   - Model Yüklendi: ❌")

        # FAISS index durumu
        print(f"\n📊 FAISS Index Durumu:")
        if hasattr(search_engine, "faiss_index") and search_engine.faiss_index:
            print(f"   - FAISS Index: ✅ ({search_engine.faiss_index.ntotal} kayıt)")
        else:
            print(f"   - FAISS Index: ❌ (Boş)")

        # Database'de kaç makale var kontrol et
        try:
            cursor = db.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            article_count = cursor.fetchone()[0]
            cursor.close()

            print(f"\n📄 Database İçeriği:")
            print(f"   - Toplam Makale: {article_count}")

            if article_count > 0:
                # Örnek makalelerden birkaçını göster
                cursor = db.connection.cursor()
                cursor.execute(
                    """
                    SELECT document_title, document_type, article_number, 
                           SUBSTR(content, 1, 100) as preview
                    FROM articles 
                    LIMIT 3
                """
                )

                sample_articles = cursor.fetchall()
                cursor.close()

                print(f"   📋 Örnek Makaleler:")
                for i, article in enumerate(sample_articles, 1):
                    print(
                        f"      {i}. {article[1]} - {article[0]} - Madde {article[2]}"
                    )
                    print(f"         Preview: {article[3]}...")

        except Exception as e:
            print(f"   ❌ Database kontrol hatası: {e}")

        # Test aramaları
        print(f"\n🧪 Test Aramaları:")

        test_queries = [
            ("vergi", "keyword"),
            ("vergi", "semantic"),
            ("vergi", "mixed"),
            ("ceza hukuku", "mixed"),
            ("mülkiyet hakları", "mixed"),
        ]

        for i, (query, search_type) in enumerate(test_queries, 1):
            print(f"\n{i}. Test: '{query}' ({search_type})")

            try:
                results = search_engine.search(
                    query=query, search_type=search_type, limit=5
                )

                if results:
                    print(f"   ✅ {len(results)} sonuç bulundu")

                    # En iyi 2 sonucu göster
                    for j, result in enumerate(results[:2], 1):
                        print(f"      {j}. Skor: {result.score:.3f}")
                        print(f"         Belge: {result.document_title}")
                        print(f"         Tür: {result.document_type}")
                        print(f"         Madde: {result.article_number}")
                        print(f"         İçerik: {result.content[:80]}...")

                else:
                    print(f"   ⚠️ Sonuç bulunamadı")

            except Exception as e:
                print(f"   ❌ Arama hatası: {e}")

        # Performance stats
        print(f"\n📊 Performans İstatistikleri:")
        try:
            stats = search_engine.get_performance_stats()
            print(f"   - Toplam Arama: {stats.get('total_searches', 0)}")
            print(
                f"   - Ortalama Süre: {stats.get('average_execution_time_ms', 0):.2f}ms"
            )
            print(f"   - FAISS Index Boyutu: {stats.get('faiss_index_size', 0)}")
            print(f"   - Cache Boyutu: {stats.get('cache_size', 0)}")
        except Exception as e:
            print(f"   ❌ Stats alma hatası: {e}")

        # Öneri sistemi test
        print(f"\n💡 Öneri Sistemi Testi:")
        try:
            suggestions = search_engine.get_suggestions("ver", 5)
            if suggestions:
                print(f"   ✅ 'ver' için öneriler: {suggestions}")
            else:
                print(f"   ℹ️ 'ver' için öneri bulunamadı")
        except Exception as e:
            print(f"   ❌ Öneri alma hatası: {e}")

        print(f"\n🎯 Semantic Search Test Sonucu:")
        if search_engine.semantic_enabled and hasattr(search_engine, "model"):
            if article_count > 0:
                print("✅ Semantic Search tamamen çalışır durumda!")
            else:
                print("⚠️ Semantic Search hazır ama database'de makale yok")
        else:
            print("⚠️ Semantic Search config'te devre dışı")

        # Database bağlantısını kapat
        db.close()

        return True

    except Exception as e:
        print(f"❌ Search Engine oluşturma hatası: {e}")
        return False


if __name__ == "__main__":
    test_semantic_search()
