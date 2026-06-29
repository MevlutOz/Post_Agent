"""make_multi.py — posts_multi.json'u editöryel '5 haber + CTA' temasında
6 PNG olarak render eder. (generate_multi.py'den sonra çalıştır.)"""
import _bootstrap  # noqa: F401
import json
from pathlib import Path
from datetime import date

from themes import editorial_multi

ROOT = Path(__file__).parent


def main():
    data = json.loads((ROOT / "data" / "posts_multi.json").read_text(encoding="utf-8"))
    cards = data.get("cards", [])
    if not cards:
        raise SystemExit("make_multi.py: posts_multi.json'da kart yok. Önce generate_multi.py.")

    today = date.today().isoformat()
    outdir = ROOT / "output" / today
    n = editorial_multi.render(cards, outdir)
    print(f"✓ {n} slayt render edildi → output/{today}/slide_1..{n}.png")


if __name__ == "__main__":
    main()
