#!/usr/bin/env python3
"""
FTS5 ve metin indexleme durumu kontrolü
"""

import os
import sqlite3
from pathlib import Path


def check_fts5_support():
    """SQLite FTS5 desteğini kontrol et"""
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE VIRTUAL TABLE test_fts USING fts5(content)")
        print("✅ FTS5 destegi mevcut")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FTS5 destegi yok: {e}")
        return False


def check_database_schema():
    """Mevcut veritabanı şemasını kontrol et"""
    db_path = Path(__file__).parent / "data" / "mevzuat.db"

    if not db_path.exists():
        print(f"❌ Veritabanı bulunamadı: {db_path}")
        return

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Tablo listesi
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tablolar: {tables}")

        # FTS tablosu var mı?
        if "articles_fts" in tables:
            print("✅ articles_fts tablosu mevcut")

            # FTS içeriği
            cursor.execute("SELECT COUNT(*) FROM articles_fts")
            fts_count = cursor.fetchone()[0]
            print(f"📊 FTS kayıt sayısı: {fts_count}")

            # Örnek veri
            cursor.execute("SELECT rowid, title FROM articles_fts LIMIT 3")
            samples = cursor.fetchall()
            print(f"📝 Örnek veriler: {samples}")

        else:
            print("❌ articles_fts tablosu yok")

        # Articles tablosu
        if "articles" in tables:
            cursor.execute("SELECT COUNT(*) FROM articles")
            articles_count = cursor.fetchone()[0]
            print(f"📊 Articles kayıt sayısı: {articles_count}")

            # content_clean alanı var mı?
            cursor.execute("PRAGMA table_info(articles)")
            columns = [row[1] for row in cursor.fetchall()]
            if "content_clean" in columns:
                print("✅ content_clean alanı mevcut")

                # content_clean dolu mu?
                cursor.execute(
                    "SELECT COUNT(*) FROM articles WHERE content_clean IS NOT NULL AND content_clean != ''"
                )
                clean_count = cursor.fetchone()[0]
                print(f"📊 Temiz içerik sayısı: {clean_count}")

                # Örnek temiz içerik
                cursor.execute(
                    "SELECT id, content_clean FROM articles WHERE content_clean IS NOT NULL AND content_clean != '' LIMIT 1"
                )
                sample = cursor.fetchone()
                if sample:
                    print(f"📝 Örnek temiz içerik: {sample[1][:100]}...")
            else:
                print("❌ content_clean alanı yok")

        conn.close()

    except Exception as e:
        print(f"❌ Veritabanı kontrolü hatası: {e}")


def test_fts_query():
    """FTS sorgu testı"""
    db_path = Path(__file__).parent / "data" / "mevzuat.db"

    if not db_path.exists():
        print("❌ Veritabanı bulunamadı, FTS test yapılamadı")
        return

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Basit FTS testi
        test_queries = ["vergi", "kanun", "madde", "türkiye"]

        for query in test_queries:
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM articles_fts WHERE articles_fts MATCH ?",
                    (query,),
                )
                count = cursor.fetchone()[0]
                print(f"🔍 '{query}' sorgusu: {count} sonuç")
            except Exception as e:
                print(f"❌ '{query}' sorgu hatası: {e}")

        conn.close()

    except Exception as e:
        print(f"❌ FTS test hatası: {e}")


def main():
    """Ana fonksiyon"""
    print("🔍 Metin İndeksleme Sistem Kontrolü")
    print("=" * 50)

    # FTS5 desteği
    print("\n1. FTS5 Desteği:")
    check_fts5_support()

    # Veritabanı şeması
    print("\n2. Veritabanı Şeması:")
    check_database_schema()

    # FTS sorgu testi
    print("\n3. FTS Sorgu Testi:")
    test_fts_query()

    print("\n" + "=" * 50)
    print("✅ Kontrol tamamlandı")


if __name__ == "__main__":
    main()
