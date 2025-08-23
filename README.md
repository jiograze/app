# Mevzuat Yönetim Sistemi

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Mevzuat Yönetim Sistemi, yasal dokümanların yönetimi, arşivlenmesi ve analizi için geliştirilmiş kapsamlı bir uygulamadır. Bu sistem, BERT tabanlı doğal dil işleme yetenekleri ile dokümanları otomatik olarak sınıflandırır ve analiz eder.

## ✨ Özellikler

- 🗂️ Doküman yönetimi ve arşivleme
- 🔍 Gelişmiş arama ve filtreleme
- 🤖 BERT tabanlı otomatik sınıflandırma
- 📊 Analitik ve raporlama
- 🔐 Rol tabanlı erişim kontrolü
- 🔄 Gerçek zamanlı güncellemeler
- 🖥️ PyQt5 tabanlı masaüstü arayüzü

## 🏗️ Proje Yapısı

```
mevzuat/
├── src/
│   └── mevzuat/               # Ana Python paketi
│       ├── api/               # API endpoint'leri
│       │   └── __init__.py
│       │
│       ├── core/              # Çekirdek iş mantığı
│       │   ├── __init__.py
│       │   ├── analyzer.py    # Metin analiz modülü
│       │   ├── app_manager.py # Uygulama yöneticisi
│       │   ├── bert.py        # BERT entegrasyonu
│       │   ├── database.py    # Veritabanı işlemleri
│       │   ├── processor.py   # Doküman işleme
│       │   ├── search.py      # Arama fonksiyonları
│       │   └── watcher.py     # Dosya değişiklik izleyici
│       │
│       ├── models/            # Veri modelleri
│       │   └── __init__.py
│       │
│       ├── monitoring/        # İzleme ve gözlemleme
│       │   ├── __init__.py
│       │   └── title_monitoring.py
│       │
│       ├── tests/             # Testler
│       │   ├── __init__.py
│       │   ├── fixtures/      # Test verileri
│       │   ├── functional/    # Fonksiyonel testler
│       │   ├── integration/   # Entegrasyon testleri
│       │   └── unit/          # Birim testleri
│       │
│       ├── training/          # Model eğitimi
│       │   ├── __init__.py
│       │   └── title_finetuner.py
│       │
│       ├── ui/                # Kullanıcı arayüzü
│       │   ├── __init__.py
│       │   ├── main_window.py # Ana pencere
│       │   ├── settings_dialog.py
│       │   └── widgets/       # Özel widget'lar
│       │
│       └── utils/             # Yardımcı fonksiyonlar
│           ├── __init__.py
│           ├── config_manager.py
│           ├── document_classifier.py
│           ├── logger.py
│           └── text_processor.py
│
├── assets/                    # Statik dosyalar
│   ├── audio/                # Ses dosyaları
│   ├── data/                 # Veri dosyaları
│   ├── fonts/                # Yazı tipleri
│   └── images/               # Resimler
│       ├── backgrounds/
│       ├── icons/
│       └── logos/
│
├── config/                   # Yapılandırma dosyaları
│   └── config.ini.example   # Örnek yapılandırma
│
├── docs/                     # Dokümantasyon
│   ├── api/                 # API dokümantasyonu
│   ├── architecture/        # Mimari dokümanlar
│   ├── development/         # Geliştirici notları
│   └── guides/              # Kullanım kılavuzları
│
├── requirements/             # Bağımlılık dosyaları
│   ├── base.txt            # Temel bağımlılıklar
│   ├── dev.txt             # Geliştirme bağımlılıkları
│   ├── prod.txt            # Üretim bağımlılıkları
│   └── test.txt            # Test bağımlılıkları
│
├── scripts/                  # Yardımcı scriptler
│   ├── analyze_and_map.py  # Kod analiz aracı
│   ├── fix_imports.py      # İçe aktarmaları düzeltme
│   ├── setup_directories.py # Dizin yapısı oluşturma
│   └── test_imports.py     # İçe aktarma testleri
│
├── .env.example             # Örnek ortam değişkenleri
├── .gitignore              # Git yapılandırması
├── pytest.ini              # Pytest yapılandırması
└── README.md               # Bu dosya
├── requirements/         # Bağımlılıklar
│   ├── base.txt          # Temel bağımlılıklar
│   ├── dev.txt           # Geliştirme bağımlılıkları
│   └── prod.txt          # Üretim bağımlılıkları
│
├── .gitignore            # Git ignore dosyası
├── setup.py              # Kurulum scripti
├── wsgi.py               # WSGI giriş noktası
└── README.md             # Bu dosya
```

## 🚀 Hızlı Başlangıç

### Ön Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- Git

### Kurulum

1. **Gereksinimler**:
   - Python 3.8 veya üzeri
   - pip (Python paket yöneticisi)
   - Git

2. Depoyu klonlayın:
   ```bash
   git clone https://github.com/yourusername/mevzuat.git
   cd mevzuat
   ```

3. Sanal ortam oluşturun ve etkinleştirin:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   ```

4. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements/base.txt
   pip install -r requirements/dev.txt  # Geliştirme için
   ```

5. Yapılandırma dosyasını oluşturun:
   ```bash
   cp .env.example .env
   # .env dosyasını düzenleyin
   ```

6. Veritabanını başlatın:
   ```bash
   python -m mevzuat.core.database init
   ```

7. Uygulamayı çalıştırın:
   ```bash
   python -m mevzuat.core.app_manager
   # Geliştirme sunucusu
   flask run
   
   # Veya doğrudan Python ile
   python wsgi.py
   ```

7. **Tarayıcıda açın:**
   ```
   http://localhost:5000
   ```

## 🧪 Testler

```bash
# Tüm testleri çalıştır
pytest

# Kapsam raporu ile test çalıştır
pytest --cov=src

# Belirli bir test modülünü çalıştır
pytest tests/unit/test_models.py -v
```

## 🛠️ Geliştirme

### Kod Stili

Kod stili kontrolü ve otomatik düzeltme için:

```bash
# Kod formatlama
black .

# İçe aktarma sıralaması
isort .

# Lint kontrolü
flake8

# Tip kontrolü
mypy .
```

### Git Commit Mesajları

[Conventional Commits](https://www.conventionalcommits.org/) formatını kullanın:

- `feat`: Yeni özellik eklendi
- `fix`: Hata düzeltmesi
- `docs`: Dokümantasyon değişiklikleri
- `style`: Kod stili düzenlemeleri
- `refactor`: Kod iyileştirmeleri
- `perf`: Performans iyileştirmeleri
- `test`: Test ekleme veya düzeltme
- `chore`: Derleme süreci veya yardımcı programlarla ilgili değişiklikler

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Fork'layın (<https://github.com/yourusername/mevzuat/fork>)
2. Özellik dalınızı oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'feat: Add some AmazingFeature'`)
4. Dalınıza push edin (`git push origin feature/AmazingFeature`)
5. Bir Pull Request açın
   ```bash
   flask db upgrade
   ```

6. Uygulamayı başlatma:
   ```bash
   flask run
   ```

## Geliştirme

- Kod stili: PEP 8
- Test çalıştırma: `pytest`
- Kod formatlama: `black .`
- Lint kontrolü: `flake8`

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakınız.
