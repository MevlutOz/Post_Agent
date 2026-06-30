# tests/test_editorial_html_multi.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from themes.editorial_html_multi import (
    build_news_card, build_cta_card, build_html_multi, build_cover_card,
)

CARDS = [
    {"kick": "AI Ofsayt", "title": f"Haber başlığı {i}",
     "body": f"Gövde metni {i}.", "source": f"Kaynak {i}"}
    for i in range(1, 6)
]

COVER = {
    "kick": "DOSYA · DÜNYA KUPASI 2026",
    "title": "Şampiyonluğun",
    "title_accent": "Görünmeyen Teknolojisi",
    "subtitle": "Bir şampiyonluğun arkasındaki SaaS & yapay zeka altyapısı: 5 ders.",
    "footer": "KAPAK DOSYASI · 5 DERS",
}


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


def test_cover_card_has_title_accent_subtitle_counter_and_image():
    html = build_cover_card(COVER, "cover-messi.jpg")
    assert 'data-screen-label="00"' in html
    assert "00 / 06" in html
    assert "Şampiyonluğun" in html
    # accent kısmı mavi span içinde
    assert "Görünmeyen Teknolojisi" in html
    assert "#0050EE" in html
    assert "SaaS &amp; yapay zeka altyapısı: 5 ders." in html
    assert "cover-messi.jpg" in html
    assert "DOSYA · DÜNYA KUPASI 2026" in html
    assert "KAPAK DOSYASI · 5 DERS" in html
    assert 'class="card"' in html


def test_cover_card_escapes_html():
    cover = {"title": "A & B", "title_accent": "<x>", "subtitle": "c & d"}
    html = build_cover_card(cover, "i.jpg")
    assert "A &amp; B" in html
    assert "&lt;x&gt;" in html
    assert "c &amp; d" in html


def test_build_html_multi_with_cover_prepends_seven_cards():
    images = {i: f"_news_{i}.png" for i in range(5)}
    html = build_html_multi(CARDS, images, cover=COVER, cover_image="cover-messi.jpg")
    assert html.count('class="card"') == 7
    assert "00 / 06" in html
    assert "cover-messi.jpg" in html
    # kapak ilk kart olmalı (CTA'dan önce)
    assert html.index('data-screen-label="00"') < html.index('data-screen-label="06"')
    # .tag stili tanımlı olmalı
    assert ".tag {" in html


def test_build_html_multi_without_cover_unchanged():
    images = {i: f"_news_{i}.png" for i in range(5)}
    html = build_html_multi(CARDS, images)
    assert html.count('class="card"') == 6
    assert "00 / 06" not in html
