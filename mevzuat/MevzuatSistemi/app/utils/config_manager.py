"""
Konfigürasyon yöneticisi - YAML dosyasını okur/yazar
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

class ConfigManager:
    """Konfigürasyon dosyalarını yöneten sınıf"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Konfigürasyon dosya yolu
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Varsayılan: exe/script yanındaki config/config.yaml
            current_dir = Path(__file__).parent.parent.parent
            self.config_path = current_dir / "config" / "config.yaml"
        
        self.sample_config_path = self.config_path.parent / "config_sample.yaml"
        self.config_data: Dict[str, Any] = {}
        
        self._load_config()
    
    def _load_config(self):
        """Konfigürasyonu yükle"""
        try:
            if self.config_path.exists():
                # Mevcut config dosyasını yükle
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f) or {}
                self.logger.info(f"Konfigürasyon yüklendi: {self.config_path}")
            else:
                # Sample'dan oluştur
                self._create_from_sample()
        except Exception as e:
            self.logger.error(f"Konfigürasyon yükleme hatası: {e}")
            self.config_data = self._get_default_config()
    
    def _create_from_sample(self):
        """Sample config'den yeni config oluştur"""
        try:
            if self.sample_config_path.exists():
                with open(self.sample_config_path, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f) or {}
                
                # Placeholder'ları değiştir
                self._replace_placeholders()
                
                # Yeni dosyayı kaydet
                self.save()
                self.logger.info("Sample'dan yeni konfigürasyon oluşturuldu")
            else:
                self.config_data = self._get_default_config()
                self.save()
                self.logger.warning("Sample config bulunamadı, varsayılan oluşturuldu")
        except Exception as e:
            self.logger.error(f"Sample config oluşturma hatası: {e}")
            self.config_data = self._get_default_config()
    
    def _replace_placeholders(self):
        """Placeholder değerleri gerçek değerlerle değiştir"""
        # Ana klasörü belirle
        if self._is_portable_mode():
            # Portable mod: exe yanındaki data klasörü
            base_folder = Path(__file__).parent.parent.parent / "data"
        else:
            # Normal mod: kullanıcı Documents klasöründe
            base_folder = Path.home() / "Documents" / "MevzuatDeposu"
        
        base_folder = base_folder.absolute()
        
        # Placeholder değiştir
        self.config_data = self._recursive_replace_placeholders(
            self.config_data, 
            "{MEVZUAT_FOLDER}", 
            str(base_folder)
        )
        
        # Diğer değerleri güncelle
        self.config_data['creation_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.config_data['user_id'] = os.getenv('USERNAME', 'user')
    
    def _recursive_replace_placeholders(self, obj: Any, placeholder: str, value: str) -> Any:
        """Nesnede placeholder'ları özyinelemeli olarak değiştir"""
        if isinstance(obj, dict):
            return {k: self._recursive_replace_placeholders(v, placeholder, value) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._recursive_replace_placeholders(item, placeholder, value) for item in obj]
        elif isinstance(obj, str):
            return obj.replace(placeholder, value)
        else:
            return obj
    
    def _is_portable_mode(self) -> bool:
        """Portable modda çalışıp çalışmadığını kontrol et"""
        try:
            # Exe yanında portable.flag dosyası varsa portable mod
            exe_dir = Path(__file__).parent.parent.parent
            return (exe_dir / "portable.flag").exists()
        except:
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Varsayılan konfigürasyonu döndür"""
        base_folder = Path.home() / "Documents" / "MevzuatDeposu"
        
        return {
            'base_folder': str(base_folder),
            'app_version': '1.0.2',
            'user_id': os.getenv('USERNAME', 'user'),
            'creation_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'watch_enabled': True,
            'watch_raw_folder': str(base_folder / "raw"),
            'logging': {
                'level': 'INFO',
                'rotate_size_mb': 5,
                'keep_files': 5
            },
            'embedding': {
                'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
                'batch_size': 32,
                'low_memory_mode': False
            },
            'search': {
                'semantic_enabled': True,
                'max_results': 20,
                'semantic_weight': 0.4,
                'keyword_weight': 0.6
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Nokta notasyonu ile değer al (örn: 'logging.level')"""
        try:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any):
        """Nokta notasyonu ile değer ayarla"""
        try:
            keys = key.split('.')
            current = self.config_data
            
            # Son anahtar dışındakileri oluştur/traverse et
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Son anahtarı ayarla
            current[keys[-1]] = value
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon ayarlama hatası: {e}")
    
    def save(self):
        """Konfigürasyonu dosyaya kaydet"""
        try:
            # Klasörü oluştur
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Dosyayı yaz
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    self.config_data, 
                    f, 
                    default_flow_style=False, 
                    allow_unicode=True,
                    sort_keys=False
                )
            
            self.logger.info(f"Konfigürasyon kaydedildi: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Konfigürasyon kaydetme hatası: {e}")
    
    def get_base_folder(self) -> Path:
        """Ana klasör yolunu Path objesi olarak döndür"""
        return Path(self.get('base_folder'))
    
    def get_raw_folder(self) -> Path:
        """Raw klasör yolunu döndür"""
        return Path(self.get('watch_raw_folder', self.get_base_folder() / 'raw'))
    
    def get_organized_folder(self) -> Path:
        """Organize edilmiş dosyalar klasörü yolunu döndür"""
        return self.get_base_folder() / 'organized'
    
    def get_db_path(self) -> Path:
        """Veritabanı dosya yolunu döndür"""
        return self.get_base_folder() / 'db' / 'mevzuat.sqlite'
    
    def get_log_folder(self) -> Path:
        """Log klasörü yolunu döndür"""
        return self.get_base_folder() / 'logs'
    
    def reload(self):
        """Konfigürasyonu yeniden yükle"""
        self._load_config()
    
    def __str__(self) -> str:
        """String temsili"""
        return f"ConfigManager(path={self.config_path}, base_folder={self.get('base_folder')})"
