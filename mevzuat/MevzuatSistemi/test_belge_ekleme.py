"""
Belge Ekleme Sistemi Test Scripti
Yeni geliştirilen belge ekleme özelliklerini test eder
"""

import os
import sys
import tempfile
from pathlib import Path

# Proje kökünü path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.utils.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager
from app.core.document_processor import DocumentProcessor

def create_test_documents():
    """Test belgeleri oluştur"""
    test_docs = []
    
    import time
    import random
    
    # Unique identifier için timestamp ve random sayı
    unique_id1 = f"{int(time.time())}_{random.randint(1000, 9999)}"
    unique_id2 = f"{int(time.time())}_{random.randint(1000, 9999)}"
    
    # Test PDF metni (basit)
    pdf_content = f"""
    TEST KANUNU - {unique_id1}
    Kanun Numarası: {random.randint(1000, 9999)}
    
    MADDE 1 - Bu kanun test amaçlı oluşturulmuştur. Test ID: {unique_id1}
    
    MADDE 2 - Test maddesinin içeriği burada yer almaktadır. 
    Bu madde ile test işlemleri yapılacaktır. Unique: {unique_id1}
    
    MADDE 3 - Bu kanun yayımı tarihinde yürürlüğe girer. ID: {unique_id1}
    """
    
    # Test TXT dosyası
    txt_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    txt_file.write(pdf_content)
    txt_file.close()
    test_docs.append(txt_file.name)
    
    # Test Word benzeri metin (farklı içerik)
    word_content = f"""
    YÖNETMELİK TEST - {unique_id2}
    Yönetmelik No: {random.randint(2000, 9999)}
    
    MADDE 1 - Amaç
    Bu yönetmeliğin amacı test işlemlerini düzenlemektir. Test ID: {unique_id2}
    
    MADDE 2 - Kapsam  
    Bu yönetmelik tüm test durumlarını kapsar. Unique: {unique_id2}
    
    MADDE 3 - Tanımlar
    Bu yönetmelikte geçen terimler şunlardır:
    a) Test: Deneme işlemi - {unique_id2}
    b) Sistem: Mevzuat yönetim platformu - {unique_id2}
    """
    
    txt_file2 = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    txt_file2.write(word_content)
    txt_file2.close()
    test_docs.append(txt_file2.name)
    
    return test_docs

def test_document_processor():
    """Document Processor'ı test et"""
    print("🔄 Document Processor testi başlatılıyor...")
    
    try:
        # Konfigürasyon
        config = ConfigManager()
        
        # Veritabanı
        db = DatabaseManager(config)
        db.initialize()
        
        # Document Processor
        processor = DocumentProcessor(config, db)
        
        # Test belgelerini oluştur
        test_files = create_test_documents()
        
        print(f"📄 {len(test_files)} test belgesi oluşturuldu")
        
        # Belgeleri işle
        results = []
        for i, file_path in enumerate(test_files, 1):
            print(f"\n📋 Test {i}: {Path(file_path).name}")
            
            result = processor.process_file(file_path)
            results.append(result)
            
            if result['success']:
                print(f"  ✅ Başarılı!")
                print(f"  📊 Document ID: {result['document_id']}")
                print(f"  📝 Madde sayısı: {result['articles_count']}")
                print(f"  📏 Metin uzunluğu: {result.get('text_length', 0)} karakter")
                print(f"  🏷️ Belge türü: {result['classification'].get('document_type', 'N/A')}")
            else:
                print(f"  ❌ Başarısız: {result['error']}")
        
        # Özet
        print(f"\n📊 TEST SONUÇLARI:")
        successful = sum(1 for r in results if r['success'])
        print(f"  ✅ Başarılı: {successful}")
        print(f"  ❌ Başarısız: {len(results) - successful}")
        
        # Veritabanı kontrolü
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM articles")  
        article_count = cursor.fetchone()[0]
        cursor.close()
        
        print(f"  📚 Toplam belge: {doc_count}")
        print(f"  📄 Toplam madde: {article_count}")
        
        # Test dosyalarını temizle
        for file_path in test_files:
            try:
                os.unlink(file_path)
            except:
                pass
        
        print(f"\n✨ Test tamamlandı!")
        
        # Veritabanı bağlantısını kapat
        db.close()
        
        return successful == len(test_files)
        
    except Exception as e:
        print(f"\n❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_duplicate_detection():
    """Duplicate detection'ı test et"""
    print("\n🔄 Duplicate detection testi...")
    
    try:
        config = ConfigManager()
        db = DatabaseManager(config)
        db.initialize()
        processor = DocumentProcessor(config, db)
        
        # Aynı dosyayı iki kez eklemeyi dene
        test_files = create_test_documents()
        file_path = test_files[0]
        
        print("📄 Dosyayı ilk kez ekleme...")
        result1 = processor.process_file(file_path)
        
        print("📄 Aynı dosyayı tekrar eklemeyi deneme...")
        result2 = processor.process_file(file_path)
        
        if result1['success'] and not result2['success']:
            print("✅ Duplicate detection çalışıyor!")
            print(f"   Hata mesajı: {result2['error']}")
            success = True
        else:
            print("❌ Duplicate detection çalışmıyor!")
            success = False
        
        # Temizlik
        for file_path in test_files:
            try:
                os.unlink(file_path)
            except:
                pass
        
        db.close()
        return success
        
    except Exception as e:
        print(f"❌ Duplicate test hatası: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 Mevzuat Sistemi - Belge Ekleme Testi")
    print("=" * 50)
    
    # Document Processor testi
    test1_success = test_document_processor()
    
    # Duplicate detection testi  
    test2_success = test_duplicate_detection()
    
    print("\n" + "=" * 50)
    print("🎯 GENEL SONUÇ:")
    print(f"   Document Processing: {'✅ BAŞARILI' if test1_success else '❌ BAŞARISIZ'}")
    print(f"   Duplicate Detection: {'✅ BAŞARILI' if test2_success else '❌ BAŞARISIZ'}")
    
    if test1_success and test2_success:
        print("\n🎉 TÜM TESTLER BAŞARILI! Sistem kullanıma hazır.")
        return True
    else:
        print("\n⚠️ BAZI TESTLER BAŞARISIZ! Lütfen hataları kontrol edin.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
