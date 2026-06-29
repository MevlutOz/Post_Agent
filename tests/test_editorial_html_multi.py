# tests/test_editorial_html_multi.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from themes.editorial_html_multi import (
    build_news_card, build_cta_card, build_html_multi,
)

CARDS = [
    {"kick": "AI Ofsayt", "title": f"Haber başlığı {i}",
     "body": f"Gövde metni {i}.", "source": f"Kaynak {i}"}
    for i in range(1, 6)
]


def test_news_card_has_title_body_source_counter_and_image():
    html = build_news_card(2, CARDS[1], "_news_1.png")
    assert "Haber başlığı 2" in html
    assert "Gövde metni 2." in html
    assert "Kaynak 2" in html
    assert "02 / 06" in html
    assert "02 — AI OFSAYT".lower() in html.lower()
    assert '_news_1.png' in html
    assert 'class="card"' in html


def test_news_card_escapes_html():
    card = {"kick": "x", "title": "A & B <tag>", "body": "c", "source": "s"}
    html = build_news_card(1, card, "i.png")
    assert "A &amp; B &lt;tag&gt;" in html
    assert "<tag>" not in html


def test_cta_card_is_fixed_png():
    html = build_cta_card()
    assert "cta-founders-investors-night.png" in html
    assert 'data-screen-label="06"' in html


def test_build_html_multi_has_six_cards_and_fixed_cta():
    images = {i: f"_news_{i}.png" for i in range(5)}
    html = build_html_multi(CARDS, images)
    assert html.count('class="card"') == 6
    assert "cta-founders-investors-night.png" in html
    # her habere kendi görseli
    for i in range(5):
        assert f"_news_{i}.png" in html
    assert "Newsreader" in html and "Space+Mono" in html


def test_build_html_multi_trims_to_five():
    images = {i: f"_news_{i}.png" for i in range(7)}
    six_cards = CARDS + [{"kick": "z", "title": "fazla", "body": "x", "source": "y"}]
    html = build_html_multi(six_cards, images)
    assert html.count('class="card"') == 6  # 5 haber + 1 CTA, fazlası kırpıldı
    assert "fazla" not in html
