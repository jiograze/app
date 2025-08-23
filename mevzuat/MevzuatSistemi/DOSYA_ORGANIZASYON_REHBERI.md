# Dosya Organizasyon Sistemi Rehberi

## Özellik Özeti

Mevzuat sistemi artık yüklediğiniz belgeleri otomatik olarak **türlerine ve numaralarına göre organize eder**. 

## Nasıl Çalışır?

### 1. Otomatik Klasör Yapısı
Yüklediğiniz belgeler şu yapıda organize edilir:

```
MevzuatDeposu/
└── organized/
    ├── kanun/
    │   └── {yıl}/
    │       └── {kanun_no}/
    ├── genelge/
    │   └── {yıl}/
    │       └── {genelge_no}/
    ├── yonetmelik/
    │   └── {yıl}/
    │       └── {yonetmelik_no}/
    ├── tuzuk/
    ├── teblig/
    ├── karar/
    └── diger/
```

### 2. Örnek Organizasyon

| Belge | Organize Yapı |
|-------|---------------|
| **2022/4 Genelge** | `organized/genelge/2022/2022-4/` |
| **2023/12 Yönetmelik** | `organized/yonetmelik/2023/2023-12/` |
| **5651 Sayılı Kanun** | `organized/kanun/2025/5651/` |

### 3. Otomatik Dosya Adlandırma
Dosyalar anlamlı şekilde yeniden adlandırılır:
- `2022-4_yonerge_dijitallesme.pdf`
- `5651_kanun_internet_ortaminda.pdf`
- `2023-12_yonetmelik_cevre_koruma.pdf`

## Konfigürasyon

### Ayarlar (config/config.yaml)
```yaml
file_organization:
  enabled: true              # Otomatik organizasyon
  delete_original: true      # Orijinal dosyayı sil
  create_year_folders: true  # Yıl klasörleri oluştur
  create_number_folders: true # Numara klasörleri oluştur
```

### Etkinleştirme/Devre Dışı Bırakma
- **Etkinleştirme**: `file_organization.enabled: true`
- **Devre Dışı**: `file_organization.enabled: false`

## Desteklenen Belge Türleri

### Otomatik Tespit Edilenler:
- ✅ **Kanun** → `kanun/` klasörü
- ✅ **Genelge/Yönerge** → `genelge/` klasörü  
- ✅ **Yönetmelik** → `yonetmelik/` klasörü
- ✅ **Tüzük** → `tuzuk/` klasörü
- ✅ **Tebliğ** → `teblig/` klasörü
- ✅ **Karar** → `karar/` klasörü

### Numara Formatları:
- `2022/4`, `2023-12` (Genelge/Yönetmelik)
- `5651 sayılı`, `No: 1234` (Kanun)
- `Sayı: 2022/15` (Genel)

## Kullanım

### 1. Raw Klasörüne Dosya Atma
```
C:\Users\[kullanıcı]\Documents\MevzuatDeposu\raw\
```
Buraya attığınız dosyalar otomatik işlenir ve organize edilir.

### 2. Sonuç Kontrolü
İşlenen dosyalar şurada bulunur:
```
C:\Users\[kullanıcı]\Documents\MevzuatDeposu\organized\
```

### 3. Log Takibi
İşlem logları:
```
C:\Users\[kullanıcı]\Documents\MevzuatDeposu\logs\app.log
```

## Sorun Giderme

### Dosya İşlenmedi
1. **Dosya formatı destekleniyor mu?**
   - PDF ✅, DOCX ✅, TXT ✅, DOC ⚠️
   
2. **Dosya boyutu çok mu büyük?**
   - Maksimum: 50MB (ayarlanabilir)
   
3. **Duplicate kontrolü**
   - Aynı dosya hash'i varsa işlenmez

### Organizasyon Sorunu  
1. **Belge türü tanınmadı**
   - `organized/diger/` klasörüne yerleştirilir
   
2. **Numara çıkarılamadı**
   - Sadece yıl klasörü oluşturulur

### Manual Test
```bash
cd MevzuatSistemi
python test_file_organization.py
```

## Gelişmiş Özellikler

### Duplicate Önleme
- MD5 hash kontrolü
- Aynı dosya iki kez işlenmez

### Akıllı Yıl Tespiti
1. Yayım tarihinden
2. Dosya adından (2022/4)
3. İçerikten otomatik çıkarım

### Esnek Klasör Yapısı
- Hierarchical: `tip/yıl/numara/`
- Flat: `tip_yıl_numara/` (gelecek)

---

## Örnek Senaryo

**Dosya**: `2022_4_dijitalleşme_genelgesi.pdf`

**İşlem Adımları**:
1. 📂 Raw klasörüne atılır
2. 🔍 İçerik analizi: "GENELGE", "Sayı: 2022/4" 
3. 🏷️ Sınıflandırma: YÖNERGE, numara: 2022-4
4. 📁 Klasör oluşturma: `organized/genelge/2022/2022-4/`
5. 📄 Dosya taşıma: `2022-4_yonerge_dijitallesme.pdf`
6. ✅ Veritabanına kayıt

**Sonuç**: 
```
organized/
└── genelge/
    └── 2022/
        └── 2022-4/
            └── 2022-4_yonerge_dijitallesme.pdf
```

Artık 2022/4 genelgeniz tam olarak `genelge/2022/2022-4/` yapısında organize edilmiştir! 🎉
