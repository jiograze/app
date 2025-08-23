# Mevzuat Belge Analiz & Sorgulama Sistemi (Yerel / Tek Kullanıcı) - Güncellenmiş Plan v2
**Son Güncelleme:** 2025-08-10 07:47:13  
**Düzenleyen:**

Bu belge, önceki tasarımın iyileştirilmiş ve genişletilmiş sürümüdür. Yapılan tüm düzeltme ve eklemeler kullanıcı deneyimini, güvenilirliği ve esnekliği artırmak için yapılandırılmıştır.

---

## 1. Temel Gereksinimler & Hedefler

### 1.1 Ana Gereksinimler
- Belgelerin yerel (offline) analizi
- Otomatik tür tespiti ve hiyerarşik klasörleme
- Madde / Geçici / Ek maddelere bölme
- Mülga / değişiklik ibarelerini işaretleme
- Tam metin + semantik arama
- Soru-cevap (RAG) özeti
- Versiyon ve diff karşılaştırması
- Klasör izleme (watcher)
- Portable ve EXE tabanlı dağıtım

### 1.2 Hedefler
| Kriter | Hedef (Yerel) |
|--------|---------------|
| Madde segmentasyonu doğruluğu | ≥ %95 |
| Mülga tespiti precision | ≥ %98 |
| Anahtar kelime arama yanıt süresi | < 400 ms |
| Semantik arama yanıt süresi | < 1.2 sn |
| İlk indeksleme (1000 madde) | < 2 dk |
| Hafıza kullanımı (1000 madde) | < 1.5 GB |
| Başlangıç açılış süresi | < 5 sn |

---

## 2. Dizin Yapısı (Esnek Path)
Kullanıcı tarafından seçilebilen ana klasör:
```
{MEVZUAT_FOLDER}/
  config/
    config.yaml
    user_preferences.json    # YENİ: kullanıcı tercihleri
  raw/                       # Kullanıcının attığı ham belgeler (watch hedefi)
  mevzuat/
    Anayasa/
    Kanun/
      4721/
        kaynak/             # Orijinal dosyalar (versiyon bazlı)
        işlenmiş/           # Düz metin (txt)
        embeddings/         # (Opsiyonel madde bazlı .npy)
        kullanıcı_notları/  # YENİ: kullanıcı tarafından eklenen notlar
    KHK/
    Tüzük/
    Yönetmelik/
    Yönerge_Genelge/
    Diger/
    _Özel_Kategoriler/      # YENİ: kullanıcı tanımlı kategoriler
  db/
    mevzuat.sqlite
    mevzuat_backup_{DATE}.sqlite  # YENİ: otomatik yedekler
  index/
    faiss.index
    embeddings.npy
    emb_map.json
  logs/
    app.log
    stats.json              # YENİ: kullanım istatistikleri
  temp/
    ocr/
    export/                 # YENİ: geçici rapor dosyaları
  quarantine/               # YENİ: işlenemeyen belgeler
  backup/                   # YENİ: yedekleme klasörü
```

---

## 3. Klasör İzleme (Watcher) Tasarımı
Bileşen: FileWatcher (Thread)
- Kütüphane: `watchdog`
- İzlenen dizin: Yapılandırılabilir (varsayılan: `raw/`)
- Olaylar: CREATED / MODIFIED
- Debounce: 2 sn (bir dosya tamamen kopyalanana kadar beklemek için boyut stabil kontrol)
- Kuyruğa ekleme: `ingest_queue` (basit Python `queue.Queue`)
- Kullanıcı arayüzünde durum listesi: Bekliyor / İşleniyor / Tamamlandı / Hata
- **YENİ**: Ağ sürücüsü desteği için path normalizasyonu
- **YENİ**: Watcher sağlık kontrolü (her 10 dk otomatik kontrol)

Pseudocode:
```python
def on_created(event):
    if event.is_directory: return
    enqueue_if_stable(event.src_path)

def enqueue_if_stable(path):
    last_size = -1
    stable_count = 0
    while stable_count < 2:
        size = os.path.getsize(path)
        if size == last_size:
            stable_count += 1
        else:
            stable_count = 0
            last_size = size
        time.sleep(1)
    # Hash kontrolü - güvenlik için
    file_hash = compute_md5(path)
    ingest_queue.put((path, file_hash))
```

---

## 4. Dosya İsimlendirme Kuralları
1. OCR gerekiyorsa hemen yapılmazsa `_ocr` etiketi eklenebilir (opsiyonel).
2. Format bileşenleri:
   - law_number veya "NA"
   - kısa başlık slug (Türkçe karakter normalize: ı->i, ş->s, ç->c, ö->o, ğ->g, ü->u)
   - versiyon (numara otomatik artar)
3. Örnek:
   - `4721_turk_medeni_kanunu_v1.pdf`
   - `NA_yonetmelik_vergi_usul_v2.docx`

Slug fonksiyonu (normalize edilmiş):
```python
def slugify(title):
    mapping = {'ı':'i','ş':'s','ç':'c','ö':'o','ğ':'g','ü':'u','İ':'I','Ş':'S','Ç':'C','Ö':'O','Ğ':'G','Ü':'U'}
    t = ''.join(mapping.get(ch, ch) for ch in title.lower())
    t = re.sub(r'[^a-z0-9]+','_', t).strip('_')
    return t[:60]  # Uzun yolları önlemek için 60 karakter sınırı
```

---

## 5. Kullanıcı Tercihleri & Kişiselleştirme (YENİ)
Aşağıdaki özellikler kullanıcı kalıcı tercihleri olarak saklanır:

### 5.1 Arama Geçmişi
- Son 50 arama sorgusu 
- Tarih damgalı (timestamp)
- Her sorguda bulunan sonuç sayısı

### 5.2 Favoriler
- Sık erişilen maddeler (bookmark)
- Özel etiketler (kişisel kategoriler)
- Hızlı erişim listesi 

### 5.3 UI Tercihleri
- Tema (Açık/Koyu/Sistem)
- Yazı tipi boyutu
- Sonuç listesi format tercihi
- Pencere konumu ve boyutu
- Panel düzeni (layout) ayarları

### 5.4 Kullanıcı Tanımlı Alanlar
- Özel kategoriler listesi
- Not şablonları
- Özel renk etiketleri

Preferences JSON örneği:
```json
{
  "user": "",
  "last_access": "2025-08-10 07:47:13",
  "ui": {
    "theme": "dark",
    "font_size": "medium",
    "layout": "horizontal_split"
  },
  "search_history": [
    {"query": "nafaka", "timestamp": "2025-08-08 14:22:10", "results": 24},
    {"query": "4721 madde 2", "timestamp": "2025-08-09 11:15:30", "results": 1}
  ],
  "favorites": [
    {"doc_id": 15, "article_id": 205, "title": "4721 Madde 185", "added": "2025-08-01"}
  ],
  "custom_categories": ["Aile Hukuku", "Özel İncelemeler"]
}
```

---

## 6. İstatistik Paneli (YENİ)
Kullanıcıya aşağıdaki istatistikleri gösteren bir dashboard:

### 6.1 Arşiv İstatistikleri
- Toplam belge sayısı (tür bazında)
- Toplam madde sayısı
- İndekslenmiş toplam token sayısı
- Arşiv boyutu (MB) ve büyüme grafiği
- Son eklenen 5 belge

### 6.2 Kullanım İstatistikleri
- En çok aranan terimler (kelime bulutu)
- En çok görüntülenen maddeler
- En çok soru sorulan konular
- Günlük/haftalık kullanım grafiği

### 6.3 Sistem İstatistikleri
- Ortalama arama yanıt süresi
- Embedding üretim performansı
- İndeks ve DB boyutu
- Disk kullanımı

---

## 7. Embedding / Indeksleme Güncellemesi
Sık güncellemeye optimize:
- Incremental embedding: Yeni eklenen maddeler için sadece append
- FAISS yeniden eğitimi yok; Flat index ekleme direkt
- Her 50 dosyada bir "compact" (yeniden yazma) opsiyonel
- **YENİ**: Düşük RAM sistemler için disk-backed indeks desteği
- **YENİ**: Büyük arşivler için chunk-bazlı incremental indeksleme

Pseudo:
```python
def add_embeddings(article_vectors, low_memory=False):
    global faiss_index
    if low_memory:
        # Parça parça ekleme - düşük RAM için
        chunk_size = 100
        for i in range(0, len(article_vectors), chunk_size):
            chunk = article_vectors[i:i+chunk_size]
            faiss_index.add(chunk)
            gc.collect()  # Bellek temizliği
    else:
        # Normal ekleme
        faiss_index.add(article_vectors)
    
    save_partial()
```

---

## 8. EXE Paketleme Stratejisi

Seçenekler:
| Araç | Artı | Eksi |
|------|------|------|
| PyInstaller | Yaygın, hızlı | Tek dosya modunda açılışta temp'e açar |
| Nuitka | Daha performanslı | Derleme süresi uzun |
| PyOxidizer | Tek binary | Öğrenme eğrisi |

Öneri: PyInstaller (OneDir + OneFile varyant)
- OneDir (klasör): Daha hızlı açılış, embedding modeli için uygun
- OneFile: Küçük dağıtım ama ilk açılış biraz yavaş

**YENİ**: Portable Mode Desteği
- Çalıştırılabilir klasör yanında data klasörü algılama
- Registry bağımsız çalışma (--portable flag)
- USB sürücü tam desteği (göreceli yollar)

Komut Örnekleri:
```
pyinstaller --noconfirm --clean --name mevzuat_app ^
  --add-data "config/config_sample.yaml;config" ^
  --add-data "models/tokenizer.json;models" ^
  --hidden-import "sentence_transformers" ^
  --add-binary "./path/to/portable_mode.dll;." ^
  app/main.py
```

Model Boyut Yönetimi:
- Varsayılan embedding modeli indirilmiyor → ilk çalıştırmada "Model indirilsin mi?" diyaloğu
- İndirme yolu: `{MEVZUAT_FOLDER}/models/`
- config.yaml'da: `embedding_model_path: "./models/all-MiniLM-L6-v2"`

Güncelleme Notu:
- EXE güncellenince sadece uygulama klasörünü değiştir; `{MEVZUAT_FOLDER}` dokunma.

---

## 9. Yedekleme Stratejisi (YENİ)

### 9.1 Otomatik Yedekleme
- SQLite DB otomatik yedekleme (periyodik)
- Varsayılan: 7 günde bir tam, günlük artımlı
- Tarih damgalı dosya adları

### 9.2 Manuel Yedekleme
- Tam arşiv yedeği: DB + raw + indeks dosyaları
- Önemli yapılandırma değişikliklerinden önce uyarı
- ZIP olarak dışa aktarma seçeneği

### 9.3 Geri Yükleme
- Tam yedekten geri yükleme sihirbazı
- Sadece DB geri yükleme seçeneği
- Seçmeli geri yükleme (sadece belirli belgeler)

```python
def backup_database(full=False):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    if full:
        backup_path = f"{config.backup_folder}/mevzuat_full_{now}.sqlite"
        # Tam DB kopyası
        shutil.copy2(config.db_path, backup_path)
        log.info(f"Tam DB yedeği oluşturuldu: {backup_path}")
    else:
        # Artımlı yedek (sadece değişiklikler)
        backup_path = f"{config.backup_folder}/mevzuat_incremental_{now}.sqlite"
        conn = sqlite3.connect(config.db_path)
        bck = sqlite3.connect(backup_path)
        conn.backup(bck)
        log.info(f"Artımlı DB yedeği oluşturuldu: {backup_path}")
```

---

## 10. Konfig Revizyonu (config.yaml)
Yeni alanlar:
```yaml
# Ana yapılandırma
base_folder: "{MEVZUAT_FOLDER}"  # Değişken kullanımı - kurulum sırasında doldurulur
app_version: "1.0.2"
user_id: ""  # YENİ: isteğe bağlı kullanıcı kimliği
creation_date: "2025-08-10 07:47:13"

# İzleme ayarları
watch_enabled: true
watch_raw_folder: "{MEVZUAT_FOLDER}/raw"
autoscan_interval_sec: 5
watch_network_paths: true  # YENİ: ağ sürücüsü desteği

# Embedding ayarları
embedding:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  download_if_missing: true
  batch_size: 32
  low_memory_mode: false  # YENİ: düşük RAM modu
  large_archive_mode: false  # YENİ: büyük arşiv modu (>10,000 belge)

# Exe ve dağıtım
exe:
  first_run_check: true
  create_default_structure: true
  portable_mode: false  # YENİ: portable mod desteği

# Yedekleme ayarları (YENİ)
backup:
  auto_backup_enabled: true
  full_backup_interval_days: 7
  incremental_backup_interval_days: 1
  keep_backups_count: 10
  backup_on_exit: false

# Kullanıcı tercihleri (YENİ)
preferences:
  save_search_history: true
  max_search_history: 50
  theme: "system"
  font_size: "medium"

# Güvenlik (YENİ)
security:
  scan_files_for_threats: true
  verify_hash_on_import: true
  password_protection: false

# Loglama
logging:
  rotate_size_mb: 5
  keep_files: 5
  detailed_stats: true  # YENİ: detaylı istatistikler

# PDF raporlama (YENİ)
reporting:
  enable_pdf_export: true
  template_folder: "{MEVZUAT_FOLDER}/templates"
  default_logo_path: "{MEVZUAT_FOLDER}/config/logo.png"
  include_header_footer: true

# Performans (YENİ/Detaylı)
performance:
  fts_pragma_optimize: true
  sqlite_cache_size_mb: 64
  sqlite_journal_mode: "WAL"  # WAL/DELETE/MEMORY
  faiss_cache_mb: 128
  threading:
    max_worker_threads: 4
    use_process_pool: false
```

---

## 11. Başlangıç (First Run) Senaryosu
1. EXE çalışır → config.yaml var mı?
   - Yoksa sihirbaz:
     - Ana klasör seç (varsayılan `C:/MevzuatDeposu` veya portableyse exe_folder/data)
     - OCR aktifle? (checkbox)
     - Model indir? (checkbox)
     - Kullanıcı ID (opsiyonel)
2. Klasör yapısı oluştur (yoksa)
3. **YENİ**: Portable mod kontrolü
   - USB sürücüde çalışıyorsa portable flag ayarla
4. "Hazır" ekranı → "Şimdi bir belge sürükleyip bırakın"
5. **YENİ**: Sistem sağlık kontrolü

---

## 12. UI (Ek Bileşenler)
- Sol panel: Klasör ağacı (Dinamik oluşturulmuş)
- Üstte base folder path gösterimi + "Değiştir" butonu (path değişince watcher reset)
- Watcher durum LED (Yeşil / Kırmızı)
- "Manuel Tara" butonu (raw klasöründeki işlenmemişleri listeler)
- Ayarlar modal:
  - OCR açık/kapalı
  - Semantik arama açık/kapalı
  - Embedding modeli durumu (indirilmiş / indir)
- Model indirme ilerleme çubuğu
- **YENİ**: İstatistik dashboardu
- **YENİ**: Yedekleme kontrol paneli
- **YENİ**: Favori maddeler bar'ı
- **YENİ**: Arşiv sağlık kontrolü / tutarlılık butonu
- **YENİ**: Belgelere not ekle / özel kategori etiketle

---

## 13. Gelişmiş Filtreleme (YENİ)
Arama ve listeleme için gelişmiş filtreleme seçenekleri:

### 13.1 Tarih Bazlı Filtreler
- Yayın tarihi aralığı
- Son değişiklik tarihi aralığı
- Yürürlük tarihi (aktif/mülga)

### 13.2 İçerik Bazlı Filtreler
- Sadece mülga maddeler
- Sadece değişiklik içerenler
- Sadece kullanıcı notu olanlar

### 13.3 Kategori Filtreleri
- Resmi sınıflandırma
- Kullanıcı tanımlı etiketler
- Kombinasyon (VE/VEYA) sorgular

```sql
-- Örnek gelişmiş filtreleme sorgusu
SELECT a.* FROM articles a
JOIN documents d ON a.document_id = d.id
LEFT JOIN user_notes n ON a.id = n.article_id
WHERE 
  d.type = 'KANUN' AND 
  d.law_number = '4721' AND
  (a.status = 'MÜLGA' OR a.status = 'AMENDED') AND
  d.effective_date BETWEEN '2020-01-01' AND '2022-12-31' AND
  (n.id IS NOT NULL OR a.custom_category_id IN (1, 3, 5))
ORDER BY a.seq_index
```

---

## 14. PDF Raporlama (YENİ)
Sonuçları ve karşılaştırmaları dışa aktarma:

### 14.1 Arama Sonuçları Raporu
- Başlıklı, sonuç maddeleri tam metinli PDF
- Kaynak bilgileri (Kanun, madde numarası)
- Opsiyonel kullanıcı notları
- Logo ve profesyonel şablon

### 14.2 Diff Raporu
- İki versiyon arasındaki değişiklikleri renk kodlu gösterim
- Değişiklik özeti tablosu
- Değişiklik tarihleri ve kaynakları

### 14.3 İstatistik Raporu
- Arşiv durum özeti
- Grafikler ve çizelgeler
- Kullanım istatistikleri

Kütüphane: `reportlab` veya `weasyprint`

```python
def generate_search_report(results, query, output_path):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    
    # Logo ve başlık
    if config.reporting.include_header_footer:
        add_header(elements, query)
    
    # Özet bilgiler
    elements.append(Paragraph(f"Sorgu: {query}", styles['Heading2']))
    elements.append(Paragraph(f"Sonuç sayısı: {len(results)}", styles['Normal']))
    elements.append(Paragraph(f"Oluşturma tarihi: {now}", styles['Normal']))
    elements.append(Paragraph(f"Kullanıcı: {config.user_id}", styles['Normal']))
    
    # Sonuçlar
    for idx, result in enumerate(results, 1):
        add_result_to_report(elements, result, idx)
    
    # PDF Oluştur
    doc.build(elements)
    return output_path
```

---

## 15. Hata Toleransı ve Karantina (YENİ)
Beklenmedik dosya ve format sorunlarına karşı:

### 15.1 Karantina Sistemi
- İşlenemeyen dosyalar `quarantine/` klasörüne taşınır
- Hata nedeni ve log kaydı birlikte saklanır
- Toplu yeniden deneme seçeneği

### 15.2 Kurtarma Mekanizmaları
- Bozuk indeks algılama ve otomatik yeniden oluşturma
- Yarım kalan işlemleri temizleme (ingest_cleanup)
- DB bütünlük kontrolü ve onarım

### 15.3 Tutarlılık Kontrol
- DB/Disk/Index uyumsuzluk kontrolü
- Orphaned madde tespiti ve çözümü
- Missing embedding tespiti

```python
def verify_consistency():
    # DB tutarlılık kontrolü
    db_check_result = verify_db_integrity()
    
    # Disk-DB tutarlılık kontrolü
    disk_db_match = verify_disk_db_match()
    
    # Embedding-DB tutarlılık kontrolü 
    emb_db_match = verify_embeddings_match()
    
    if not all([db_check_result, disk_db_match, emb_db_match]):
        generate_inconsistency_report()
        return False
    
    return True
```

---

## 16. Güvenlik Önlemleri (YENİ)
Veri bütünlüğü ve güvenlik artırımları:

### 16.1 Dosya Bütünlük Kontrolü
- Import/ingest sırasında hash kontrolü (MD5/SHA256)
- İndeks ve DB dosyaları için checksum

### 16.2 Zararlı İçerik Kontrolü
- Makro içeren Office dosyaları tespiti
- JavaScript içeren PDF tespiti
- VBA veya diğer potansiyel komut içeriği taraması

### 16.3 Erişim Kontrolü
- Opsiyonel parola koruması
- Hassas not ve özel kategorileri şifreleme

```python
def verify_file_integrity(file_path, expected_hash=None):
    computed_hash = compute_file_hash(file_path)
    
    if expected_hash and computed_hash != expected_hash:
        log.warning(f"Hash uyuşmazlığı: {file_path}")
        return False
    
    # Zararlı içerik kontrolü
    if file_path.endswith(('.docx', '.doc')):
        if contains_macros(file_path):
            log.warning(f"Makro içeren belge: {file_path}")
            return False
    
    # PDF güvenlik kontrolü
    if file_path.endswith('.pdf'):
        if contains_javascript(file_path):
            log.warning(f"JavaScript içeren PDF: {file_path}")
            return False
    
    return True
```

---

## 17. Lisanslama & Telif Bilgileri (YENİ)
Yasal ve etik uyarılar:

### 17.1 Uygulama Lisansı
- Açık kaynak lisans bilgisi (MIT / GPL / vb.)
- Ticari kullanım kısıtları (varsa)

### 17.2 İçerik Telif Uyarısı
- Mevzuat içeriği kullanım kısıtları
- Kamusal belgelerin kullanımı yasal bildirimi
- Metinlerin dağıtım kısıtları

### 17.3 Veri Koruma
- Kullanıcı ekli notlar için KVKK uygunluğu
- Kişisel veri içerebilecek alanlar için önlemler

```
Telif Notu:
Bu yazılım, {LICENSE} altında lisanslanmıştır.

Mevzuat metinleri, Türkiye Cumhuriyeti ilgili kurumları tarafından yayınlanan kamusal belgelerdir. 
Bu içeriklerin kullanımı kendi yasal düzenlemelerine tabidir.

Bu yazılım, mevzuat metinlerini veya bu metinlere erişimi düzenleyen yasalara 
uygunluğu garanti etmez. Kullanıcı, ilgili içeriğin kullanımından sorumludur.

Son güncelleme: 2025-08-10
Kullanıcı:
```

---

## 18. Kullanıcı Tanımlı Ek Alan Desteği (YENİ)
Kullanıcıların belgeleri zenginleştirmesi için:

### 18.1 Özel Kategori Sistemi
- Kullanıcı tanımlı kategoriler ve alt kategoriler
- Kategorilere renk kodları atama
- Hiyerarşik kategori görüntüleme

### 18.2 Not ve Açıklamalar
- Madde ve belge seviyesinde kullanıcı notları
- Zengin metin formatı (bold, italik, liste)
- Kaynakça ekleme

### 18.3 İlişkilendirme
- Maddeler arası kullanıcı tanımlı bağlantılar
- "Bunu görenler şunları da gördü" tarzı ilişkilendirme
- Benzer madde önerileri

DB Schema Eklentileri:
```sql
-- Kullanıcı kategorileri
CREATE TABLE user_categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#808080',
    parent_id INTEGER NULL REFERENCES user_categories(id),
    created_at TEXT
);

-- Madde notları
CREATE TABLE user_notes (
    id INTEGER PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    document_id INTEGER REFERENCES documents(id),
    title TEXT,
    content TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- Madde-kategori ilişkileri
CREATE TABLE article_categories (
    article_id INTEGER REFERENCES articles(id),
    category_id INTEGER REFERENCES user_categories(id),
    PRIMARY KEY (article_id, category_id)
);

-- Kullanıcı tanımlı ilişkiler
CREATE TABLE article_relations (
    source_id INTEGER REFERENCES articles(id),
    target_id INTEGER REFERENCES articles(id),
    relation_type TEXT,
    created_at TEXT,
    PRIMARY KEY (source_id, target_id)
);
```

---

## 19. Donanım Önerisi (Güncellenen)
| Ölçek | CPU | RAM | Disk | Not |
|-------|-----|-----|------|-----|
| 5–10 Kanun | 2 çekirdek | 4 GB | <1 GB | Temel kullanım |
| 100+ Kanun | 4 çekirdek | 8 GB | 2–4 GB | Genel kullanım |
| 1000+ Kanun | 6+ çekirdek | 16 GB | 10+ GB | Büyük arşiv |
| LLM yerel (7B quant) | 6+ çekirdek | 16+ GB | +6–8 GB model | Çevrimdışı RAG |

### Düşük RAM Modu Özellikleri
- FAISS'te hafif indeks (IndexFlatIP yerine IndexLSH)
- Batch işleme boyutu küçültme
- SQLite pragmas (cache_size düşürme)
- Garbage collection daha agresif

### Yüksek Performans Modu
- Çoklu işçi (worker) paralelleştirme
- Önbellek boyutları artırma
- Hızlı indeks türleri (IndexIVFFlat)
- SSD diskte tutma önerisi

---

## 20. Gelişmiş Ölçüm & Diagnostic
Sistem sağlığı ve performans izleme:

### 20.1 Performans Metrikleri
- Belge işleme süresi (ms/belge)
- Arama yanıt süresi (p50, p95, p99)
- Embedding üretme hızı (tokens/sn)
- Disk I/O (oku/yaz)

### 20.2 Sağlık Kontrolleri
- DB integrity check
- Orphaned record check
- Missing file check
- Duplicate madde/kanun kontrolü

### 20.3 Diagnostic Log
- Log seviyesi dinamik ayarlama
- Geri bildirim hataları (errors.jsonl)
- Performans zaman damgalı kayıt

```python
def log_performance_metric(operation, duration_ms, details=None):
    metric = {
        "timestamp": datetime.now().isoformat(),
        "user": config.user_id,
        "operation": operation,
        "duration_ms": duration_ms,
        "details": details or {}
    }
    
    with open(f"{config.log_path}/performance.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(metric) + "\n")
```

---

## 21. Portable Mode İyileştirmeleri (YENİ)
USB sürücü ve taşınabilir cihazlarda tam destek:

### 21.1 Göreceli Yol Kullanımı
- Tüm dosya yolları exe klasörüne göreceli
- `os.path.dirname(sys.executable)` temel alınır
- "%appdata%" yerine yerel klasör

### 21.2 Registry Bağımsızlık
- Hiçbir ayar registry'de saklanmaz
- Yapılandırma dosyası exe konumu + /config/

### 21.3 Otomatik Algılama
- Exe konumu USB sürücüdeyse otomatik portable mod
- Taşınabilir cihazlar için disk şifresi desteği (opsiyonel)

```python
def is_running_from_removable_drive():
    exe_path = os.path.dirname(sys.executable)
    try:
        drive_letter = os.path.splitdrive(exe_path)[0]
        if not drive_letter:
            return False
        
        import win32api
        drive_type = win32api.GetDriveType(drive_letter)
        # DRIVE_REMOVABLE = 2
        return drive_type == 2
    except:
        return False

def get_base_dir():
    if config.exe.portable_mode or is_running_from_removable_drive():
        # Exe yanındaki data klasörü
        return os.path.join(os.path.dirname(sys.executable), "data")
    else:
        # Kullanıcının seçtiği klasör
        return config.base_folder
```

---

## 22. Dağıtım / Yayın Notları
1. Geliştirme modunda: `python app/main.py`
2. Build: `pyinstaller build.spec`
3. Çıktı:
   - `dist/mevzuat_app/mevzuat_app.exe` (OneDir)
   - `dist/mevzuat_app.exe` (OneFile)
4. Kullanıcıya verilecek:
   - `mevzuat_app/` klasörü veya tek `mevzuat_app.exe`
   - README (kurulum + ilk çalıştırma)
5. İlk çalışma:
   - Klasör seç → otomatik config üret → watcher başlat
6. Güncelleme:
   - Eski exe klasörünü sil → yeni sürümü koy (data klasörü etkilenmez)

---

## 23. Undo Güncellemesi
- Path tabanlı değişiklikler (dosya adı normalizasyonu) için snapshot:
  - Önce: raw/original.pdf
  - Sonra: mevzuat/Kanun/4721/kaynak/4721_turk_medeni_kanunu_v1.pdf
- Geri alma: sadece metadata + DB düzeltme (fiziksel dosyayı eski yerine kopyalama) (opsiyonel uyarı: "Dizin değişiklikleri için geri yükleme tam olmayabilir")
- **YENİ**: Tüm işlem tipleri için destek
- **YENİ**: İnteraktif işlem tarihçesi görüntüleme

---

## 24. Gelecek (Opsiyonel) Basit Ekler
- Tray icon (Windows system tray) → Watcher çalışıyor göstergesi
- Otomatik güncelleme bildirimi (manuel kontrol)
- Kanun türü manuel seçim override (dropdown + yeniden indeksle)
- **YENİ**: İlgili içtihat kararlarını gösteren sekme (opsiyonel)
- **YENİ**: PDF içinde metni highlight edebilme
- **YENİ**: Birebir aynı madde için fıkra karşılaştırma
- **YENİ**: Export API - veri çıktısı format (JSON/XML)
- **YENİ**: GPT-3.5 uyumlu API (araştırma projelerine entegrasyon)

---

## 25. Örnek Geliştirilmiş config_sample.yaml
```yaml
# Ana yapılandırma - Temel Klasör (kurulum sırasında yerleştirilir)
base_folder: "{MEVZUAT_FOLDER}"
app_version: "1.0.2"
user_id: ""
creation_date: "2025-08-10 07:47:13"

# İzleme ayarları
watch_enabled: true
watch_raw_folder: "{MEVZUAT_FOLDER}/raw"
autoscan_interval_sec: 5
watch_network_paths: true
watch_health_check_min: 10

# OCR ve metin çıkarma
ocr:
  enabled: false
  tesseract_path: "C:/Program Files/Tesseract-OCR/tesseract.exe"
  enable_layout_analysis: true
  confidence_threshold: 75
  lang: "tur"

# Embedding ayarları
embedding:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  download_if_missing: true
  batch_size: 32
  low_memory_mode: false
  large_archive_mode: false
  cache_embeddings: true

# Arama ayarları
search:
  semantic_enabled: true
  max_results: 20
  highlight_matches: true
  include_repealed: false
  cache_size: 100
  semantic_weight: 0.4
  keyword_weight: 0.6

# Versiyonlama
versioning:
  fuzzy_title_threshold: 0.8
  allow_duplicate_versions: false
  auto_diff_on_new_version: true
  store_diff_results: true

# Exe ve dağıtım
exe:
  first_run_check: true
  create_default_structure: true
  portable_mode: false
  splash_screen: true
  tray_icon: true

# Yedekleme ayarları
backup:
  auto_backup_enabled: true
  full_backup_interval_days: 7
  incremental_backup_interval_days: 1
  keep_backups_count: 10
  backup_on_exit: false
  compress_backups: true

# Kullanıcı tercihleri
preferences:
  save_search_history: true
  max_search_history: 50
  theme: "system"
  font_size: "medium"
  layout: "default"
  max_favorites: 100
  save_window_position: true

# Undo/geri alma
undo:
  max_items: 20
  include_file_operations: true
  warn_on_complex_undo: true

# Güvenlik
security:
  scan_files_for_threats: true
  verify_hash_on_import: true
  password_protection: false
  encrypt_user_notes: false
  password_hash: ""

# Loglama
logging:
  level: "INFO"
  rotate_size_mb: 5
  keep_files: 5
  detailed_stats: true
  performance_logging: true
  log_search_queries: true

# PDF raporlama
reporting:
  enable_pdf_export: true
  template_folder: "{MEVZUAT_FOLDER}/templates"
  default_logo_path: "{MEVZUAT_FOLDER}/config/logo.png"
  include_header_footer: true
  default_font: "DejaVuSans"
  company_name: ""

# RAG ve soru yanıtlama
rag:
  enabled: true
  max_chunks: 8
  max_chunk_chars: 1200
  model_type: "local"  # local/api
  local_model_path: "{MEVZUAT_FOLDER}/models/llm"
  api_key: ""
  api_url: ""
  prompt_template_path: "{MEVZUAT_FOLDER}/config/prompts/default.txt"

# Kullanıcı tanımlı alanlar
custom_fields:
  enabled: true
  max_categories: 50
  max_notes_per_article: 20
  rich_text_notes: true

# Performans
performance:
  fts_pragma_optimize: true
  sqlite_cache_size_mb: 64
  sqlite_journal_mode: "WAL"  # WAL/DELETE/MEMORY
  faiss_cache_mb: 128
  threading:
    max_worker_threads: 4
    use_process_pool: false
  cleanup_interval_hours: 24
  temp_file_ttl_days: 7
```

---

## 26. Sonuç
Bu güncel plan:
- Yerel, tek kullanıcılı ve portable bir EXE uygulaması
- Belirli klasör yapısında otomatik organizasyon
- Zengin metin analizi ve semantik arama
- Kullanıcı özelleştirme ve tercihleri
- Veri güvenliği ve bütünlüğü
için eksiksiz bir çözüm sunar.

Uygulama, hukuk metinlerini verimli şekilde organize etmek, aramak ve ilişkilendirmek isteyen bireysel kullanıcılar için tam donanımlı, esnek ve güvenilir bir çözüm olarak tasarlanmıştır.

İlk kurulum ve kullanıma başlama için sadece:
1. EXE'yi çalıştır
2. Klasör yolu seç (veya varsayılanı kabul et)
3. "Raw" klasörüne mevzuat dosyalarını at
4. Hiyerarşik organizasyon, arama ve sorgulama sisteminden yararlan

---

**Son Güncelleme:** 2025-08-10 07:47:13  
**Güncelleme Yapan:**