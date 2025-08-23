"""
Gelişmiş logging sistemi - dosya rotasyonu ve farklı seviyeler
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logger(name: str, config_manager=None) -> logging.Logger:
    """
    Gelişmiş logger kur
    
    Args:
        name: Logger adı
        config_manager: Konfigürasyon yöneticisi (opsiyonel)
    
    Returns:
        Yapılandırılmış logger
    """
    logger = logging.getLogger(name)
    
    # Zaten yapılandırılmışsa tekrar yapılandırma
    if logger.handlers:
        return logger
    
    # Varsayılan ayarlar
    log_level = logging.INFO
    log_folder = Path("logs")
    rotate_size_mb = 5
    keep_files = 5
    
    # Config manager varsa ayarları al
    if config_manager:
        log_level_str = config_manager.get('logging.level', 'INFO')
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        log_folder = config_manager.get_log_folder()
        rotate_size_mb = config_manager.get('logging.rotate_size_mb', 5)
        keep_files = config_manager.get('logging.keep_files', 5)
    
    # Log klasörünü oluştur
    log_folder.mkdir(parents=True, exist_ok=True)
    
    # Logger seviyesini ayarla
    logger.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Dosya handler (rotating)
    log_file = log_folder / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=rotate_size_mb * 1024 * 1024,  # MB to bytes
        backupCount=keep_files,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler (sadece WARNING ve üzeri)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # İlk log mesajı
    logger.info(f"Logger başlatıldı: {name}")
    
    return logger


def setup_performance_logger(config_manager=None) -> logging.Logger:
    """
    Performans metrikleri için ayrı logger
    
    Returns:
        Performans logger'ı
    """
    logger = logging.getLogger("performance")
    
    if logger.handlers:
        return logger
    
    # Ayarlar
    log_folder = Path("logs")
    if config_manager:
        log_folder = config_manager.get_log_folder()
    
    log_folder.mkdir(parents=True, exist_ok=True)
    
    logger.setLevel(logging.INFO)
    
    # Performans formatter (JSON benzeri)
    perf_formatter = logging.Formatter(
        '{"timestamp":"%(asctime)s","operation":"%(name)s","message":"%(message)s"}',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Performans dosya handler
    perf_file = log_folder / "performance.jsonl"
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(perf_formatter)
    logger.addHandler(perf_handler)
    
    return logger


def log_performance_metric(operation: str, duration_ms: float, details: dict = None):
    """
    Performans metriği kaydet
    
    Args:
        operation: İşlem adı
        duration_ms: Süre (milisaniye)
        details: Ek detaylar
    """
    perf_logger = logging.getLogger("performance")
    
    message_parts = [f"duration_ms={duration_ms:.2f}"]
    
    if details:
        for key, value in details.items():
            message_parts.append(f"{key}={value}")
    
    message = ", ".join(message_parts)
    perf_logger.info(message, extra={"name": operation})


class TimedOperation:
    """Context manager ile işlem süresi ölçme"""
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None, details: dict = None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger("performance")
        self.details = details or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
            
            # Hata varsa detaylara ekle
            if exc_type:
                self.details['error'] = str(exc_val)
                self.details['error_type'] = exc_type.__name__
            
            log_performance_metric(self.operation_name, duration_ms, self.details)


# Kullanım örneği:
"""
# Basit kullanım
logger = setup_logger("my_module")
logger.info("Modül başlatıldı")

# Performans ölçümü
with TimedOperation("document_processing", details={"file_size": 1024}):
    # İşlem kodu buraya
    pass

# Manuel performans kaydı
log_performance_metric("search_query", 250.5, {"results_count": 15})
"""
