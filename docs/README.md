# Mevzuat Yönetim Sistemi

Mevzuat Yönetim Sistemi, yasal dokümanların yönetimi, aranması ve analizi için geliştirilmiş kapsamlı bir doküman yönetim sistemidir.

## Özellikler

- **Belge Yönetimi**: PDF, Word, Excel ve diğer formatlarda belge yükleme ve saklama
- **Metin Çıkarma**: OCR ve doğrudan metin çıkarma desteği
- **Gelişmiş Arama**: Tam metin arama ve anlamsal arama
- **Belge Kategorizasyonu**: Otomatik belge kategorizasyonu
- **API**: RESTful API ile entegrasyon
- **Web Arayüzü**: Kullanıcı dostu web arayüzü

## Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- PostgreSQL (önerilen) veya SQLite
- Poppler-utils (PDF işlemleri için)
- Tesseract OCR (isteğe bağlı, tarama belgeleri için)

### Kurulum Adımları

1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/yourusername/mevzuat.git
   cd mevzuat
   ```

2. Sanal ortam oluşturun ve etkinleştirin:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # veya
   .\venv\Scripts\activate  # Windows
   ```

3. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements/base.txt
   # Geliştirme için ek bağımlılıklar:
   pip install -r requirements/dev.txt
   ```

4. Yapılandırma dosyasını oluşturun:
   ```bash
   cp config/development.yaml.example config/development.yaml
   ```
   `config/development.yaml` dosyasını düzenleyerek veritabanı bağlantı bilgilerinizi ve diğer ayarları yapılandırın.

5. Veritabanını başlatın:
   ```bash
   flask db upgrade
   ```

6. Uygulamayı çalıştırın:
   ```bash
   flask run
   ```

7. Tarayıcıda `http://localhost:5000` adresine giderek uygulamayı görüntüleyin.

## Geliştirme

### Kod Stili

Kod stilini kontrol etmek için:
```bash
black .
flake8
mypy .
```

### Testler

Testleri çalıştırmak için:
```bash
pytest
```

### API Dokümantasyonu

API dokümantasyonu Swagger UI üzerinden `http://localhost:5000/api/docs` adresinde mevcuttur.

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın.
