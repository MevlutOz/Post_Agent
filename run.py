"""
run.py — Tüm pipeline'ı tek komutla çalıştırır.
Kullanım:  python run.py   (ya da çift tık: calistir.bat)
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
steps = [
    ("1/5  Haberler toplanıyor (RSS)",        "fetch.py"),
    ("2/5  Claude aday haberleri hazırlıyor",  "curate.py"),
    ("3/5  Haber seçimi (sen seçeceksin)",     "secim.py"),
    ("4/5  Claude carousel metni üretiyor",    "generate.py"),
    ("5/5  Slayt görselleri hazırlanıyor",     "make_image.py"),
]
for label, script in steps:
    print(f"\n{'='*50}\n{label}\n{'='*50}", flush=True)
    r = subprocess.run([sys.executable, str(ROOT / script)])
    if r.returncode != 0:
        print(f"\n✗ Hata: {script} adımında durdu.")
        sys.exit(1)

print("\n✅ Bitti. Çıktılar output/<tarih>/ klasöründe "
      "(captions.md + slide_1..N.png)")
