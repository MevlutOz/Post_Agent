"""
select.py — Adayları terminalde listeler, kullanıcıdan TEK haber seçtirir.
Çıktı: data/curated.json (tek elemanlı liste)
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import json
from pathlib import Path

ROOT = Path(__file__).parent


def parse_choice(raw, n):
    """'1'..'n' arası geçerli girdiyi 0-tabanlı indekse çevirir, yoksa None."""
    raw = (raw or "").strip()
    if not raw.lstrip("-").isdigit():
        return None
    v = int(raw)
    if 1 <= v <= n:
        return v - 1
    return None
