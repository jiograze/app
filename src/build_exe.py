"""
PyInstaller build script - EXE oluşturma
Mevzuat Belge Analiz & Sorgulama Sistemi
"""

import os
import shutil
import sys
from pathlib import Path


def build_exe():
    """EXE dosyası oluştur"""

    # Proje kökü
    project_root = Path(__file__).parent

    # Build parametreleri
    app_name = "MevzuatSistemi"
    main_script = "main.py"
    icon_path = "assets/icon.ico"  # Varsa

    # PyInstaller komutu
    build_command = [
        "pyinstaller",
        "--name",
        app_name,
        "--windowed",  # GUI app, konsol gösterme
        "--onedir",  # Tek klasörde
        "--noconfirm",  # Onay isteme
        "--clean",  # Temiz build
        # Dahil edilecek dosyalar
        "--add-data",
        "app;app",
        "--add-data",
        "config;config",
        "--add-data",
        "assets;assets",
        # Dahil edilecek modüller
        "--hidden-import",
        "PyQt5.QtCore",
        "--hidden-import",
        "PyQt5.QtGui",
        "--hidden-import",
        "PyQt5.QtWidgets",
        "--hidden-import",
        "sentence_transformers",
        "--hidden-import",
        "faiss",
        "--hidden-import",
        "sklearn",
        "--hidden-import",
        "nltk",
        "--hidden-import",
        "docx",
        "--hidden-import",
        "fitz",
        "--hidden-import",
        "pdfplumber",
        "--hidden-import",
        "pytesseract",
        "--hidden-import",
        "watchdog",
        # Dışlanacaklar
        "--exclude-module",
        "matplotlib.tests",
        "--exclude-module",
        "numpy.tests",
        "--exclude-module",
        "PIL.tests",
        # Ana script
        main_script,
    ]

    # Icon varsa ekle
    if os.path.exists(icon_path):
        build_command.extend(["--icon", icon_path])

    # Build klasörünü temizle
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    # PyInstaller'ı çalıştır
    print("PyInstaller ile EXE oluşturuluyor...")
    print(" ".join(build_command))

    result = os.system(" ".join(build_command))

    if result == 0:
        print(f"\n✅ Build başarılı!")
        print(f"EXE dosyası: dist/{app_name}/{app_name}.exe")

        # Portable sürüm için gerekli dosyaları kopyala
        dist_path = Path(f"dist/{app_name}")

        # Config şablonları
        config_source = Path("config")
        if config_source.exists():
            shutil.copytree(config_source, dist_path / "config", dirs_exist_ok=True)

        # Klasör yapısı oluştur
        folders = ["raw", "processed", "quarantine", "logs", "models", "temp"]
        for folder in folders:
            (dist_path / folder).mkdir(exist_ok=True)

        # README ve lisans dosyalarını kopyala
        for file in ["README.md", "LICENSE", "CHANGELOG.md"]:
            if os.path.exists(file):
                shutil.copy(file, dist_path)

        print("📁 Portable klasör yapısı oluşturuldu")

    else:
        print("❌ Build başarısız!")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
