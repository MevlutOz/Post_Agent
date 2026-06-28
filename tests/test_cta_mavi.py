# tests/test_cta_mavi.py
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from themes import cta_mavi

SAMPLE = {
    "cover_title": "Tek atılım, 3 milyar dolar",
    "cover_subtitle": "Menlo Ventures'ın Anthropic atılımı zirveyle sonuçlandı.",
    "slides": [
        {"heading": "Ne oldu?", "body": "Menlo 3 milyar dolarlık fonunu kapattı."},
        {"heading": "Neden önemli?", "body": "Tek doğru karar itibarı kurar."},
        {"heading": "Kuruculara ne anlama geliyor?", "body": "Sermaye en güçlü inanandan akar."},
    ],
    "cta_title": "Sen olsan firmanı tek adıma yatırır mıydın?",
    "cta_subtitle": "Takip et: @saasbridge",
    "source": "TechCrunch",
}


def test_render_writes_five_slides_1080x1350(tmp_path):
    n = cta_mavi.render(SAMPLE, tmp_path)
    assert n == 5
    files = sorted(tmp_path.glob("slide_*.png"))
    assert len(files) == 5
    for f in files:
        with Image.open(f) as im:
            assert im.size == (1080, 1350)
