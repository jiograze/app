"""
Dosya izleme sistemi - klasörleri otomatik takip eder
"""

import os
import time
import hashlib
from pathlib import Path
from threading import Thread, Event
from queue import Queue, Empty
from typing import Optional, Callable
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

class MevzuatFileHandler(FileSystemEventHandler):
    """Mevzuat dosyaları için özel event handler"""
    
    def __init__(self, ingest_queue: Queue, logger: logging.Logger):
        super().__init__()
        self.ingest_queue = ingest_queue
        self.logger = logger
        self.processing_files = set()  # İşlenmekte olan dosyalar
        
        # Desteklenen dosya uzantıları
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.txt'}
    
    def on_created(self, event):
        """Dosya oluşturulduğunda çağrılır"""
        if not event.is_directory and self._is_supported_file(event.src_path):
            self.logger.info(f"Yeni dosya algılandı: {event.src_path}")
            self._enqueue_file_after_stable(event.src_path)
    
    def on_modified(self, event):
        """Dosya değiştirildiğinde çağrılır"""
        if not event.is_directory and self._is_supported_file(event.src_path):
            # Sadece yeni dosyaları işle (mevcut olanların sürekli modified eventi gelmesini önle)
            if event.src_path not in self.processing_files:
                self.logger.info(f"Dosya değişikliği algılandı: {event.src_path}")
                self._enqueue_file_after_stable(event.src_path)
    
    def _is_supported_file(self, file_path: str) -> bool:
        """Dosya uzantısının desteklenip desteklenmediğini kontrol et"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def _enqueue_file_after_stable(self, file_path: str):
        """Dosya kararlı hale geldikten sonra kuyruğa ekle"""
        # Threading ile dosya kararlılığını kontrol et
        def check_and_enqueue():
            try:
                if self._wait_for_file_stable(file_path):
                    file_hash = self._compute_file_hash(file_path)
                    
                    self.processing_files.add(file_path)
                    self.ingest_queue.put({
                        'path': file_path,
                        'hash': file_hash,
                        'timestamp': time.time()
                    })
                    
                    self.logger.info(f"Dosya kuyruğa eklendi: {file_path}")
                else:
                    self.logger.warning(f"Dosya kararlı hale gelmedi: {file_path}")
                    
            except Exception as e:
                self.logger.error(f"Dosya kuyruk hatası: {file_path} - {e}")
        
        # Arka plan thread'i başlat
        thread = Thread(target=check_and_enqueue, daemon=True)
        thread.start()
    
    def _wait_for_file_stable(self, file_path: str, max_wait: int = 10) -> bool:
        """Dosyanın kararlı hale gelmesini bekle"""
        last_size = -1
        stable_count = 0
        wait_count = 0
        
        while stable_count < 3 and wait_count < max_wait:  # 3 kez aynı boyutta ise kararlı
            try:
                if not os.path.exists(file_path):
                    return False
                
                current_size = os.path.getsize(file_path)
                
                if current_size == last_size:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_size = current_size
                
                time.sleep(1)
                wait_count += 1
                
            except (OSError, IOError) as e:
                self.logger.warning(f"Dosya boyutu okunamıyor: {file_path} - {e}")
                time.sleep(1)
                wait_count += 1
        
        return stable_count >= 3
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Dosya MD5 hash'i hesapla"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                chunk_size = 8192
                
                while chunk := f.read(chunk_size):
                    file_hash.update(chunk)
                
                return file_hash.hexdigest()
                
        except Exception as e:
            self.logger.error(f"Hash hesaplama hatası: {file_path} - {e}")
            return ""
    
    def mark_file_processed(self, file_path: str):
        """Dosyayı işlenmiş olarak işaretle"""
        self.processing_files.discard(file_path)


class FileWatcher:
    """Klasör izleme ve dosya işleme yöneticisi"""
    
    def __init__(self, config_manager, document_processor):
        self.config = config_manager
        self.document_processor = document_processor
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # İzleme ayarları
        self.watch_folder = config_manager.get_raw_folder()
        self.scan_interval = config_manager.get('autoscan_interval_sec', 5)
        self.health_check_interval = config_manager.get('watch_health_check_min', 10) * 60
        
        # Threading
        self.observer: Optional[Observer] = None
        self.ingest_queue = Queue()
        self.processor_thread: Optional[Thread] = None
        self.health_check_thread: Optional[Thread] = None
        self.stop_event = Event()
        
        # Handler
        self.file_handler = MevzuatFileHandler(self.ingest_queue, self.logger)
        
        # İstatistikler
        self.stats = {
            'files_processed': 0,
            'files_failed': 0,
            'last_activity': None,
            'is_healthy': True
        }
    
    def start_watching(self):
        """Dosya izlemeyi başlat"""
        try:
            # İzleme klasörünün varlığını kontrol et
            if not self.watch_folder.exists():
                self.watch_folder.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"İzleme klasörü oluşturuldu: {self.watch_folder}")
            
            # Watchdog observer'ı başlat
            self.observer = Observer()
            self.observer.schedule(
                self.file_handler, 
                str(self.watch_folder), 
                recursive=True
            )
            
            self.observer.start()
            self.logger.info(f"Dosya izleme başlatıldı: {self.watch_folder}")
            
            # İşleme thread'ini başlat
            self.processor_thread = Thread(target=self._process_queue, daemon=True)
            self.processor_thread.start()
            
            # Sağlık kontrolü thread'ini başlat
            self.health_check_thread = Thread(target=self._health_check, daemon=True)
            self.health_check_thread.start()
            
            # İlk tarama (mevcut dosyalar için)
            self._initial_scan()
            
        except Exception as e:
            self.logger.error(f"Dosya izleme başlatma hatası: {e}")
            raise
    
    def stop_watching(self):
        """Dosya izlemeyi durdur"""
        try:
            self.logger.info("Dosya izleme durduruluyor...")
            
            # Stop event'ini ayarla
            self.stop_event.set()
            
            # Observer'ı durdur
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
            
            # Thread'lerin bitmesini bekle
            if self.processor_thread and self.processor_thread.is_alive():
                self.processor_thread.join(timeout=5)
            
            if self.health_check_thread and self.health_check_thread.is_alive():
                self.health_check_thread.join(timeout=5)
            
            self.logger.info("Dosya izleme durduruldu")
            
        except Exception as e:
            self.logger.error(f"Dosya izleme durdurma hatası: {e}")
    
    def _initial_scan(self):
        """İlk tarama - mevcut dosyaları kontrol et"""
        try:
            self.logger.info("İlk tarama başlatılıyor...")
            
            for file_path in self.watch_folder.rglob('*'):
                if file_path.is_file() and self.file_handler._is_supported_file(str(file_path)):
                    # Dosya zaten işlenmiş mi kontrol et
                    if not self._is_file_already_processed(file_path):
                        file_hash = self.file_handler._compute_file_hash(str(file_path))
                        
                        self.ingest_queue.put({
                            'path': str(file_path),
                            'hash': file_hash,
                            'timestamp': time.time(),
                            'initial_scan': True
                        })
            
            self.logger.info("İlk tarama tamamlandı")
            
        except Exception as e:
            self.logger.error(f"İlk tarama hatası: {e}")
    
    def _is_file_already_processed(self, file_path: Path) -> bool:
        """Dosyanın daha önce işlenip işlenmediğini kontrol et"""
        # Bu kontrol veritabanından yapılabilir
        # Şimdilik basit - dosya adına göre kontrol
        # TODO: Veritabanı ile entegrasyon
        return False
    
    def _process_queue(self):
        """Kuyruktan dosyaları işle"""
        self.logger.info("Dosya işleme thread'i başlatıldı")
        
        while not self.stop_event.is_set():
            try:
                # Kuyruktaki dosyayı al (5 saniye timeout)
                try:
                    file_info = self.ingest_queue.get(timeout=5)
                except Empty:
                    continue
                
                # Dosyayı işle
                success = self._process_file(file_info)
                
                # İstatistikleri güncelle
                if success:
                    self.stats['files_processed'] += 1
                else:
                    self.stats['files_failed'] += 1
                
                self.stats['last_activity'] = time.time()
                
                # İşlenmiş olarak işaretle
                self.file_handler.mark_file_processed(file_info['path'])
                
                # Queue task done
                self.ingest_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Kuyruk işleme hatası: {e}")
                continue
        
        self.logger.info("Dosya işleme thread'i sonlandırıldı")
    
    def _process_file(self, file_info: dict) -> bool:
        """Tek dosyayı işle"""
        file_path = file_info['path']
        
        try:
            self.logger.info(f"Dosya işleniyor: {file_path}")
            
            # Dosyanın hala var olduğunu kontrol et
            if not os.path.exists(file_path):
                self.logger.warning(f"Dosya bulunamadı: {file_path}")
                return False
            
            # Document processor ile işle
            result = self.document_processor.process_file(file_path)
            
            if result['success']:
                self.logger.info(f"Dosya başarıyla işlendi: {file_path}")
                
                # Başarılı ise dosyayı taşı (opsiyonel)
                if self.config.get('watch.move_processed_files', False):
                    self._move_processed_file(file_path, result)
                
                return True
            else:
                self.logger.error(f"Dosya işleme başarısız: {file_path} - {result.get('error', 'Bilinmeyen hata')}")
                
                # Başarısız ise karantinaya taşı
                self._move_to_quarantine(file_path, result.get('error', 'Bilinmeyen hata'))
                return False
                
        except Exception as e:
            self.logger.error(f"Dosya işleme exception: {file_path} - {e}")
            self._move_to_quarantine(file_path, str(e))
            return False
    
    def _move_processed_file(self, file_path: str, result: dict):
        """İşlenmiş dosyayı hedefe taşı"""
        try:
            # Organizasyon sonucu varsa bilgi ver
            if 'organization' in result and result['organization'].get('success'):
                org_info = result['organization']
                self.logger.info(f"Dosya organize edildi:")
                self.logger.info(f"  Kaynak: {file_path}")
                self.logger.info(f"  Hedef: {org_info.get('target_path', 'N/A')}")
                self.logger.info(f"  Klasör yapısı: {org_info.get('organized_structure', 'N/A')}")
            else:
                # Eski yöntem - processed klasörüne taşı
                processed_folder = self.config.get_base_folder() / 'processed'
                processed_folder.mkdir(parents=True, exist_ok=True)
                
                source_path = Path(file_path)
                target_path = processed_folder / source_path.name
                
                if target_path.exists():
                    timestamp = int(time.time())
                    target_path = processed_folder / f"{source_path.stem}_{timestamp}{source_path.suffix}"
                
                source_path.rename(target_path)
                self.logger.info(f"Dosya processed klasörüne taşındı: {target_path}")
                
        except Exception as e:
            self.logger.error(f"Dosya taşıma hatası: {file_path} - {e}")
    
    def _move_to_quarantine(self, file_path: str, error_reason: str):
        """Başarısız dosyayı karantinaya taşı"""
        try:
            quarantine_folder = self.config.get_base_folder() / 'quarantine'
            quarantine_folder.mkdir(parents=True, exist_ok=True)
            
            source_path = Path(file_path)
            target_path = quarantine_folder / source_path.name
            
            # Eğer aynı isimde dosya varsa timestamp ekle
            if target_path.exists():
                timestamp = int(time.time())
                target_path = quarantine_folder / f"{source_path.stem}_{timestamp}{source_path.suffix}"
            
            source_path.rename(target_path)
            
            # Hata log dosyası oluştur
            error_log_path = target_path.with_suffix('.error.log')
            with open(error_log_path, 'w', encoding='utf-8') as f:
                f.write(f"Dosya: {source_path}\n")
                f.write(f"Hata Zamanı: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Hata: {error_reason}\n")
            
            self.logger.info(f"Dosya karantinaya taşındı: {target_path}")
            
        except Exception as e:
            self.logger.error(f"Karantina taşıma hatası: {file_path} - {e}")
    
    def _health_check(self):
        """Sağlık kontrolü thread'i"""
        while not self.stop_event.is_set():
            try:
                # Observer'ın çalışıp çalışmadığını kontrol et
                if self.observer and not self.observer.is_alive():
                    self.stats['is_healthy'] = False
                    self.logger.error("File observer çalışmıyor!")
                else:
                    self.stats['is_healthy'] = True
                
                # Belirli süre boyunca aktivite yoksa uyar
                if self.stats['last_activity']:
                    time_since_activity = time.time() - self.stats['last_activity']
                    if time_since_activity > self.health_check_interval:
                        self.logger.warning(f"Son {self.health_check_interval/60:.1f} dakikada dosya aktivitesi yok")
                
                # Sağlık kontrol aralığında bekle
                self.stop_event.wait(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Sağlık kontrolü hatası: {e}")
                self.stop_event.wait(60)  # Hata durumunda 1 dakika bekle
    
    def get_status(self) -> dict:
        """Watcher durumunu döndür"""
        return {
            'is_watching': self.observer is not None and self.observer.is_alive(),
            'watch_folder': str(self.watch_folder),
            'queue_size': self.ingest_queue.qsize(),
            'stats': self.stats.copy(),
            'is_healthy': self.stats['is_healthy']
        }
    
    def manual_scan(self) -> int:
        """Manuel tarama başlat"""
        self.logger.info("Manuel tarama başlatıldı")
        
        files_added = 0
        for file_path in self.watch_folder.rglob('*'):
            if file_path.is_file() and self.file_handler._is_supported_file(str(file_path)):
                if not self._is_file_already_processed(file_path):
                    file_hash = self.file_handler._compute_file_hash(str(file_path))
                    
                    self.ingest_queue.put({
                        'path': str(file_path),
                        'hash': file_hash,
                        'timestamp': time.time(),
                        'manual_scan': True
                    })
                    
                    files_added += 1
        
        self.logger.info(f"Manuel tarama tamamlandı: {files_added} dosya eklendi")
        return files_added
