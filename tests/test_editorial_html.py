# tests/test_editorial_html.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from themes.editorial_html import (
    color_last_clause, build_image_prompt, card_payload, build_html,
)

POST = {
    "cover_title": "Tek atılım, 3 milyar dolar",
    "cover_subtitle": "Menlo'nun Anthropic atılımı zirveyle sonuçlandı.",
    "slides": [
        {"heading": "Ne oldu?", "body": "Menlo 3 milyar dolarlık fonunu kapattı."},
        {"heading": "Neden önemli?", "body": "Tek doğru karar itibarı kurar."},
        {"heading": "Kuruculara ne anlama geliyor?", "body": "Sermaye inanandan akar."},
    ],
    "cta_title": "Sen olsan firmanı tek adıma yatırır mıydın?",
    "source": "TechCrunch",
}
IMAGES = {"hero": "_img_hero.png", "move": "_img_move.png",
          "founder": "_img_founder.png", "investor": "_img_investor.png"}


def test_color_last_clause_wraps_last_segment():
    out = color_last_clause("Tek atılım, 3 milyar dolar")
    assert "<span" in out and "#0050EE" in out
    assert "3 milyar dolar" in out


def test_color_last_clause_no_separator_is_plain():
    assert "<span" not in color_last_clause("Tek büyük atılım")


def test_color_last_clause_escapes_html():
    assert "<script>" not in color_last_clause("a, <script>")


def test_build_image_prompt_is_bw_editorial():
    p = build_image_prompt("VC yatırımı").lower()
    assert "black and white" in p
    assert "no text" in p


def test_card_payload_fills_missing():
    cp = card_payload({"cover_title": "x", "slides": [], "source": "S"})
    assert cp["cover_subtitle"] == ""
    assert len(cp["slides"]) == 3
    assert cp["slides"][0]["body"] == ""


def test_build_html_full_structure():
    html = build_html(POST, IMAGES)
    assert html.count('data-screen-label') == 6
    assert "image-slot" not in html          # düz <img> kullanıldı
    assert "feTurbulence" in html            # grain SVG
    assert "Newsreader" in html              # font linki
    assert POST["cover_title"].split(",")[0] in html
    assert "_img_hero.png" in html
    assert "_img_founder.png" in html and "_img_investor.png" in html
    assert "YORUMLARDA BULUŞALIM" in html
    assert "cta-founders-investors-night.png" in html
