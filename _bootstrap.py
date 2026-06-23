"""
_bootstrap.py — Her adımın en başında import edilir.

Yaptıkları:
  1) .env dosyasındaki API anahtarlarını ortam değişkenlerine yükler
     (ANTHROPIC_API_KEY, WIRO_API_KEY, WIRO_API_SECRET ...).
  2) Windows konsolunda Türkçe/emoji karakterlerinin (→ ✓ ✅) çökmemesi için
     stdout/stderr'i UTF-8'e ayarlar.

Kullanım: ilgili scriptin en üstünde `import _bootstrap`  yazman yeterli.
"""
import sys
from pathlib import Path

# 1) .env yükle
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass  # python-dotenv yoksa ortam değişkenleri zaten tanımlıysa çalışır

# 2) UTF-8 çıktı (Windows cp1254 sorununu çözer)
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass
