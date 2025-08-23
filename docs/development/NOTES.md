# Mevzuat Sistemi - Geliştirme Notları

## 📋 TODO Listesi

### Yüksek Öncelik
- [ ] Ana UI penceresi (PyQt5)
- [ ] Arama arayüzü implementasyonu  
- [ ] Sonuç gösterme widget'ları
- [ ] FAISS embedding entegrasyonu
- [ ] Semantik arama algoritması

### Orta Öncelik
- [ ] Settings/Preferences dialog
- [ ] File watcher UI kontrolleri
- [ ] Progress bar ve durum göstergeleri
- [ ] Error handling ve user feedback
- [ ] Database migration sistem

### Düşük Öncelik  
- [ ] OCR modülü test
- [ ] PDF rapor şablonları
- [ ] Backup/restore UI
- [ ] Portable mode detector
- [ ] System tray integration

## 🐛 Bilinen Sorunlar

1. **Import Hatası**: Bazı modüller henüz yazılmamış
   - `app.core.search_engine` eksik
   - `app.ui.main_window` eksik

2. **Bağımlılıklar**: Opsiyonel paketler
   - PyMuPDF (fitz) - PDF işleme için
   - Tesseract - OCR için
   - sentence-transformers - Embedding için

3. **Platform**: Şimdilik sadece Windows

## 🔧 Teknik Detaylar

### Veritabanı Şeması
- SQLite FTS5 ile tam metin arama
- FAISS ile semantik indeksleme
- İlişkisel tablolar (documents, articles, etc.)

### Threading Model
- Ana UI thread
- File watcher thread  
- Document processor thread
- Search worker threads

### Konfigürasyon
- YAML tabanlı ayarlar
- Runtime'da değiştirilebilir
- Portable mode desteği

## 📊 Performance Hedefleri

| Metrik | Hedef |
|--------|--------|
| Startup time | < 5 sn |
| Search response | < 400 ms (keyword) |
| Semantic search | < 1.2 sn |
| File processing | < 2 dk/1000 madde |
| Memory usage | < 1.5 GB |

## 🎯 Mimari Kararlar

### Neden PyQt5?
- Native look & feel
- Threading desteği
- Zengin widget seti
- Python entegrasyonu

### Neden SQLite?
- Serverless
- ACID uyumlu
- FTS5 desteği
- Portable

### Neden FAISS?
- Hızlı similarity search
- Düşük bellek kullanımı
- CPU optimized
- Incremental indexing

## 📚 Referanslar

### Kütüphaneler
- [PyQt5 Docs](https://doc.qt.io/qtforpython-5/)
- [FAISS Tutorial](https://github.com/facebookresearch/faiss/wiki)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
- [Sentence Transformers](https://www.sbert.net/)

### Mevzuat Kaynakları
- Resmi Gazete
- Mevzuat.gov.tr API
- TBMM Kanun Teklifi formatları

---
**Son Güncelleme**: 2025-08-10  
**Geliştirici**:
