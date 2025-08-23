"""
README - Mevzuat Belge Analiz & Sorgulama Sistemi
"""

# Mevzuat Belge Analiz & Sorgulama Sistemi v1.0.2

Bu proje, mevzuat belgelerini yerel ortamda otomatik olarak işleyip sorgulama imkanı sunan bir masaüstü uygulamasıdır.

## 🚀 Özellikler

### Ana Özellikler
- **Otomatik Dosya İzleme**: Raw klasörüne atılan belgeler otomatik işlenir
- **Çoklu Format Desteği**: PDF, DOCX, DOC, TXT dosyalarını okur
- **Akıllı Sınıflandırma**: Belge türünü (Kanun, Tüzük, Yönetmelik vb.) otomatik tespit eder
- **Madde Ayrıştırma**: Belgeleri madde madde ayırır ve analiz eder
- **Mülga/Değişiklik Tespiti**: Değişen ve mülga maddeleri otomatik tespit eder
- **Semantik Arama**: Anlam tabanlı arama yapabilir
- **Full Text Search**: Hızlı metin bazlı arama
- **Kullanıcı Notları**: Maddeler üzerine not ekleme
- **PDF Raporlama**: Arama sonuçlarını PDF olarak dışa aktarma

### Teknik Özellikler
- SQLite veritabanı ile yerel veri depolama
- FAISS ile semantik indeksleme
- PyQt5 tabanlı kullanıcı arayüzü
- Watchdog ile klasör izleme
- OCR desteği (Tesseract)
- Multi-threading ile performans
- EXE olarak tek dosya dağıtımı

## 📋 Gereksinimler

### Minimum Sistem Gereksinimleri
- **OS**: Windows 10+ (64-bit)
- **RAM**: 4 GB (8 GB önerilen)
- **Disk**: 2 GB boş alan
- **CPU**: 2 çekirdek (4 çekirdek önerilen)

### Python Sürümü (Geliştirme için)
- Python 3.8+
- Gerekli kütüphaneler: `requirements.txt` dosyasında listelendi

## 🛠️ Kurulum

### Son Kullanıcı (EXE)
1. `MevzuatSistemi.exe` dosyasını indirin
2. Çift tıklayarak çalıştırın
3. İlk çalışmada kurulum sihirbazını takip edin
4. Ana klasörünüzü seçin (varsayılan: `Documents/MevzuatDeposu`)
5. OCR ve embedding modellerini indirip indirmeyeceğinizi seçin

### Geliştirici Kurulumu
```bash
# Projeyi klonlayın
git clone <repo-url>
cd MevzuatSistemi

# Virtual environment oluşturun
python -m venv venv
venv\Scripts\activate  # Windows

# Gereksinimleri kurun
pip install -r requirements.txt

# Uygulamayı çalıştırın
python main.py
```

## 📁 Dizin Yapısı

Kurulum sonrası ana klasör yapısı:
```
MevzuatDeposu/
├── config/                 # Konfigürasyon dosyaları
├── raw/                    # Ham belgeler (buraya dosya atın)
├── mevzuat/               # İşlenmiş belgeler
│   ├── Anayasa/
│   ├── Kanun/
│   ├── KHK/
│   ├── Tüzük/
│   ├── Yönetmelik/
│   └── ...
├── db/                    # SQLite veritabanı
├── index/                 # FAISS indeksleri
├── logs/                  # Log dosyaları
├── backup/                # Otomatik yedekler
└── temp/                  # Geçici dosyalar
```

## 🎯 Kullanım

### İlk Kurulum
1. **Klasör Seçimi**: Verilerinizin saklanacağı ana klasörü seçin
2. **Model İndirme**: Semantik arama için embedding modeli indirin (350 MB)
3. **OCR Kurulumu**: PDF'lerden metin çıkarmak için Tesseract'ı kurun (opsiyonel)

### Belge Ekleme
1. `raw/` klasörüne PDF, DOCX veya TXT dosyalarınızı atın
2. Sistem otomatik olarak dosyaları algılar ve işler
3. İşleme durumunu ana penceredeki durum çubuğundan takip edin

### Arama Yapma
1. Ana penceredeki arama kutusuna sorgunuzu yazın
2. Arama türünü seçin:
   - **Anahtar Kelime**: Tam metin arama
   - **Semantik**: Anlam bazlı arama
   - **Karışık**: Her ikisini de kullan
3. Sonuçları inceleyin ve detayına tıklayın

### Filtreleme
- **Belge Türü**: Kanun, Tüzük, Yönetmelik vb.
- **Tarih Aralığı**: Yayın/yürürlük tarihi
- **Durum**: Aktif, mülga, değişiklik
- **Kategori**: Kullanıcı tanımlı kategoriler

### Not Ekleme
1. Herhangi bir maddeye sağ tıklayın
2. "Not Ekle" seçeneğini seçin
3. Notunuzu yazın ve kaydedin
4. Notlar arama sonuçlarında görüntülenir

## ⚙️ Konfigürasyon

Ana ayarlar `config/config.yaml` dosyasında:

```yaml
# Ana ayarlar
base_folder: "C:/MevzuatDeposu"
watch_enabled: true

# Arama ayarları
search:
  semantic_enabled: true
  max_results: 20
  semantic_weight: 0.4
  keyword_weight: 0.6

# OCR ayarları
ocr:
  enabled: false
  tesseract_path: "C:/Program Files/Tesseract-OCR/tesseract.exe"

# Performans ayarları
performance:
  sqlite_cache_size_mb: 64
  max_worker_threads: 4
```

## 🔧 Gelişmiş Özellikler

### OCR (Optik Karakter Tanıma)
- Taranmış PDF'lerden metin çıkarır
- Tesseract OCR motoru kullanır
- Türkçe dil desteği
- Güven eşiği ile kalite kontrolü

### Embedding ve Semantik Arama
- Sentence Transformers ile metin vektorizasyonu
- FAISS ile hızlı benzerlik araması
- Türkçe dil modeli desteği
- İnkremental indeksleme

### Yedekleme Sistemi
- Otomatik günlük/haftalık yedekler
- Manuel yedekleme seçenekleri
- Compress edilmiş yedek dosyaları
- Seçici geri yükleme

### PDF Raporlama
- Arama sonuçlarını PDF'e aktarma
- Özelleştirilebilir şablonlar
- Logo ve başlık ekleme
- Diff raporları

## 🚨 Sorun Giderme

### Yaygın Sorunlar

**1. Dosyalar işlenmiyor**
- `raw/` klasörü doğru yolda mı kontrol edin
- File Watcher durumu yeşil mi kontrol edin
- Log dosyalarını inceleyin (`logs/app.log`)

**2. Arama sonuç vermiyor**
- Veritabanında veri var mı kontrol edin
- İndeksleme tamamlandı mı kontrol edin
- Arama terimlerini değiştirip deneyin

**3. OCR çalışmıyor**
- Tesseract kurulu mu kontrol edin
- Path ayarları doğru mu kontrol edin
- Türkçe dil paketi yüklü mü kontrol edin

**4. Performans sorunları**
- RAM kullanımını kontrol edin
- Çok büyük dosyaları parçalara bölün
- Low memory mode'u aktifleştirin

### Log Dosyaları
- **Ana Log**: `logs/app.log`
- **Performans**: `logs/performance.jsonl`
- **Hata Detayları**: `logs/error.log`

## 🔗 Ek Araçlar

### Portable Mod
EXE'yi USB'de çalıştırmak için:
1. `portable.flag` dosyası oluşturun (EXE yanında)
2. Veriler `data/` klasöründe saklanır
3. Registry bağımsız çalışır

### Komut Satırı
```bash
# Manuel tarama
MevzuatSistemi.exe --scan

# Yedekleme
MevzuatSistemi.exe --backup

# Veritabanı bakımı
MevzuatSistemi.exe --vacuum
```

## 📊 İstatistikler

Sistem şu metrikleri takip eder:
- İşlenen belge sayısı
- Toplam madde sayısı
- Arama sorgu istatistikleri
- Performans metrikleri
- Kullanım sıklığı

## 🔒 Güvenlik

### Veri Güvenliği
- Tüm veriler yerel olarak saklanır
- İsteğe bağlı parola koruması
- Dosya bütünlük kontrolü (hash)
- Zararlı içerik tarama

### Gizlilik
- İnternet bağlantısı gerektirmez
- Harici veri gönderimi yok
- Kullanıcı verilerinin şifrelenmesi
- KVKK uyumlu veri işleme

## 🆘 Destek

### Dokümantasyon
- Wiki sayfaları
- Video eğitimleri
- FAQ bölümü
- API referansı

### Topluluk
- GitHub Issues
- Tartışma forumu
- E-posta desteği

## 📜 Lisans

Bu proje MIT lisansı altında yayınlanmıştır. Detaylar için `LICENSE` dosyasını inceleyiniz.

### Telif Uyarısı
Mevzuat metinleri Türkiye Cumhuriyeti ilgili kurumları tarafından yayınlanan kamusal belgelerdir. Bu içeriklerin kullanımı kendi yasal düzenlemelerine tabidir.

## 🎉 Teşekkürler

Bu proje şu açık kaynak projeleri kullanmaktadır:
- PyQt5 (GUI)
- Sentence Transformers (NLP)
- FAISS (Vector Search)
- Watchdog (File Monitoring)
- SQLite (Database)
- Tesseract (OCR)

---

**Son Güncelleme**: 2025-08-10  
**Versiyon**: 1.0.2  
**Geliştirici**:
