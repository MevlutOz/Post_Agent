"""make_multi.py — posts_multi.json'u editöryel '5 haber + CTA' temasında
6 PNG olarak render eder. (generate_multi.py'den sonra çalıştır.)"""
import _bootstrap  # noqa: F401
import json
import os
import sys
from pathlib import Path
from datetime import date

from themes import editorial_multi

ROOT = Path(__file__).parent


def main():
    data = json.loads((ROOT / "data" / "posts_multi.json").read_text(encoding="utf-8"))
    cards = data.get("cards", [])
    if not cards:
        raise SystemExit("make_multi.py: posts_multi.json'da kart yok. Önce generate_multi.py.")

    # Opsiyonel kapak: posts_multi.json'daki "cover" bloğu + foto yolu
    # (CLI arg ya da COVER_IMAGE env). Foto yoksa kapak atlanır.
    cover = data.get("cover")
    cover_img = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("COVER_IMAGE")
    if cover and not cover_img:
        print("  ! 'cover' tanımlı ama kapak fotoğrafı verilmedi (arg/COVER_IMAGE); kapak atlanıyor.")
        cover = None

    today = date.today().isoformat()
    outdir = ROOT / "output" / today
    n = editorial_multi.render(cards, outdir, cover=cover, cover_image_src=cover_img if cover else None)
    print(f"✓ {n} slayt render edildi → output/{today}/slide_1..{n}.png")


if __name__ == "__main__":
    main()
