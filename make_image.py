"""make_image.py — run_config.json'daki temaya göre carousel render eder.
  theme=cta_mavi  → themes/cta_mavi.py (saf Pillow, mevcut tema)
  theme=editorial → themes/editorial.py (Playwright, WIRED editöryel)
İçerik data/posts.json'dan gelir."""
import _bootstrap  # noqa: F401
import json
from pathlib import Path
from datetime import date

from runconfig import load_run_config

ROOT = Path(__file__).resolve().parent


def main():
    post = json.loads((ROOT / "data" / "posts.json").read_text(encoding="utf-8"))
    cfg = load_run_config(ROOT / "data" / "run_config.json")
    theme = cfg["theme"]
    outdir = ROOT / "output" / date.today().isoformat()

    if theme == "editorial":
        from themes import editorial
        n = editorial.render(post, outdir)
    else:
        from themes import cta_mavi
        n = cta_mavi.render(post, outdir)

    print(f"\nCarousel hazır: {outdir}  ({n} slayt, tema={theme})")


if __name__ == "__main__":
    main()
