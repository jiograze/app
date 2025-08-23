#!/usr/bin/env python3
"""
Dosya organizasyon sistemi test scripti
"""

import os
import sys
from pathlib import Path
import tempfile
import shutil

# Ana dizin ve app paketini path'e ekle
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.utils.config_manager import ConfigManager
from app.core.document_processor import DocumentProcessor
from app.core.database_manager import DatabaseManager

def create_test_files():
    """Test dosyaları oluştur"""
    test_files = []
    
    # Geçici klasör oluştur
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Test dosyaları: {temp_dir}")
    
    # Test dosya içerikleri
    test_documents = [
        {
            'filename': '2022-4_genelge.txt',
            'content': '''
            GENELGE
            Sayı: 2022/4
            
            Kamu Kurum ve Kuruluşlarında Dijitalleşme Genelgesi
            
            MADDE 1 - Bu genelgenin amacı kamu kurumlarında dijitalleşme süreçlerini 
            düzenlemektir.
            
            MADDE 2 - Bu genelge yayımlandığı tarih itibariyle yürürlüğe girer.
            
            15 Mart 2022
            '''
        },
        {
            'filename': '2023-12_yonetmelik.txt',
            'content': '''
            YÖNETMELİK
            
            Çevre Koruma Yönetmeliği
            Yönetmelik No: 2023/12
            
            Yayım Tarihi: 10 Haziran 2023
            
            MADDE 1 - Bu yönetmelik çevre koruma faaliyetlerini düzenler.
            
            MADDE 2 - Yürürlük tarihi 1 Temmuz 2023'tür.
            '''
        },
        {
            'filename': '5651_sayili_kanun.txt',
            'content': '''
            5651 SAYILI KANUN
            
            İnternet Ortamında Yapılan Yayınların Düzenlenmesi ve Bu Yayınlar 
            Yoluyla İşlenen Suçlarla Mücadele Edilmesi Hakkında Kanun
            
            MADDE 1 - Bu Kanunun amacı, internet ortamında yapılan yayınların 
            düzenlenmesidir.
            
            Yürürlük: 4 Mayıs 2007
            '''
        }
    ]
    
    # Test dosyalarını oluştur
    for doc in test_documents:
        file_path = temp_dir / doc['filename']
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(doc['content'])
        test_files.append(file_path)
    
    return test_files, temp_dir

def test_file_organization():
    """Dosya organizasyonu testini çalıştır"""
    print("=== DOSYA ORGANİZASYON TESTİ ===\n")
    
    try:
        # Test dosyalarını oluştur
        test_files, temp_dir = create_test_files()
        
        # Config ve bileşenleri hazırla
        config = ConfigManager()
        print(f"Ana klasör: {config.get_base_folder()}")
        print(f"Organize klasör: {config.get_organized_folder()}")
        
        # Database manager
        db_manager = DatabaseManager(config)
        db_manager.initialize()
        
        # Document processor
        doc_processor = DocumentProcessor(config, db_manager)
        
        print("\n=== TEST DOSYALARI İŞLENİYOR ===\n")
        
        for test_file in test_files:
            print(f"\nİşleniyor: {test_file.name}")
            print("-" * 50)
            
            # Dosyayı işle
            result = doc_processor.process_file(str(test_file))
            
            if result.get('success'):
                print("✓ İşleme başarılı")
                print(f"  Belge türü: {result['classification'].get('document_type', 'N/A')}")
                print(f"  Başlık: {result['classification'].get('title', 'N/A')}")
                print(f"  Kanun No: {result['classification'].get('law_number', 'N/A')}")
                print(f"  Madde sayısı: {result.get('articles_count', 0)}")
                
                # Organizasyon bilgileri
                if 'organization' in result:
                    org = result['organization']
                    if org.get('success'):
                        print("✓ Dosya organizasyonu başarılı")
                        print(f"  Hedef klasör: {org.get('organized_structure', 'N/A')}")
                        print(f"  Tam yol: {org.get('target_path', 'N/A')}")
                    else:
                        print(f"✗ Organizasyon hatası: {org.get('error', 'N/A')}")
                else:
                    print("ℹ Dosya organizasyonu devre dışı")
            else:
                print(f"✗ İşleme hatası: {result.get('error', 'N/A')}")
        
        print("\n=== ORGANIZE EDİLMİŞ KLASÖR YAPISI ===\n")
        
        # Organize klasörü içeriğini göster
        organized_folder = config.get_organized_folder()
        if organized_folder.exists():
            show_folder_structure(organized_folder, organized_folder)
        else:
            print("Organize klasörü henüz oluşturulmamış")
        
    except Exception as e:
        print(f"Test hatası: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Temizlik
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"\nGeçici dosyalar temizlendi: {temp_dir}")

def show_folder_structure(path, base_path, indent=0):
    """Klasör yapısını göster"""
    if not path.exists():
        return
    
    items = sorted(path.iterdir())
    for item in items:
        prefix = "  " * indent + "├── " if indent > 0 else ""
        
        if item.is_dir():
            rel_path = item.relative_to(base_path)
            print(f"{prefix}📁 {rel_path}")
            show_folder_structure(item, base_path, indent + 1)
        else:
            rel_path = item.relative_to(base_path)
            size = item.stat().st_size
            print(f"{prefix}📄 {rel_path} ({size} bytes)")

if __name__ == "__main__":
    test_file_organization()
