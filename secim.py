"""
secim.py — Adayları terminalde listeler, kullanıcıdan TEK haber seçtirir.
(Not: dosya adı stdlib `select` modülünü gölgelememek için `secim`dir.)
Çıktı: data/curated.json (tek elemanlı liste)
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import json
from pathlib import Path

ROOT = Path(__file__).parent


def parse_choice(raw, n):
    """'1'..'n' arası geçerli girdiyi 0-tabanlı indekse çevirir, yoksa None."""
    raw = (raw or "").strip()
    try:
        v = int(raw)
    except ValueError:
        return None
    if 1 <= v <= n:
        return v - 1
    return None


def format_candidate(i, c):
    """Tek adayı numaralı, detaylı blok olarak biçimler."""
    summary = (c.get("summary") or "").strip()
    if len(summary) > 220:
        summary = summary[:220].rstrip() + "…"
    lines = [
        f"{i}) [{c.get('source','?')}] {c.get('title','').strip()}",
    ]
    if summary:
        lines.append(f"     Özet: {summary}")
    if c.get("reason"):
        lines.append(f"     Neden ilgi çekici: {c['reason']}")
    if c.get("angle"):
        lines.append(f"     Önerilen açı: {c['angle']}")
    return "\n".join(lines)


def main():
    cand_path = ROOT / "data" / "candidates.json"
    if not cand_path.exists():
        print("✗ data/candidates.json yok. Önce curate.py çalıştırılmalı.")
        raise SystemExit(1)

    candidates = json.loads(cand_path.read_text(encoding="utf-8"))
    if not candidates:
        print("✗ Aday haber listesi boş. fetch/curate adımlarını kontrol et.")
        raise SystemExit(1)

    n = len(candidates)
    print("\n" + "=" * 60)
    print("  Bu haftanın haber adayları")
    print("=" * 60)
    for i, c in enumerate(candidates, 1):
        print()
        print(format_candidate(i, c))
    print()

    while True:
        raw = input(f"Hangi haberi post yapalım? (1-{n}): ")
        idx = parse_choice(raw, n)
        if idx is not None:
            break
        print(f"  ! Geçersiz giriş. 1 ile {n} arasında bir numara gir.")

    chosen = candidates[idx]
    (ROOT / "data" / "curated.json").write_text(
        json.dumps([chosen], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✓ Seçildi: {chosen.get('title','')[:70]}")
    print("  → data/curated.json yazıldı.")


if __name__ == "__main__":
    main()
