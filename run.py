"""
run.py — Tüm pipeline'ı tek komutla çalıştırır.
Kullanım:  ANTHROPIC_API_KEY=... python3 run.py
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
steps = [
    ("1/4  Haberler toplanıyor (RSS)",      "fetch.py"),
    ("2/4  Claude haberleri seçiyor",        "curate.py"),
    ("3/4  Claude post metinleri üretiyor",  "generate.py"),
    ("4/4  Görseller hazırlanıyor",          "make_image.py"),
]
for label, script in steps:
    print(f"\n{'='*50}\n{label}\n{'='*50}")
    r = subprocess.run([sys.executable, str(ROOT / script)])
    if r.returncode != 0:
        print(f"\n✗ Hata: {script} adımında durdu.")
        sys.exit(1)

print("\n✅ Bitti. Çıktılar output/<tarih>/ klasöründe (captions.md + post_*.png)")
