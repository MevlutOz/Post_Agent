# themes/editorial_multi.py
"""N haber + sabit CTA editöryel render: her haber için Wiro S/B fotoğrafı,
Playwright(Chromium) → kart sayısı + 1 PNG (kapak varsa +1). editorial.py render mantığıyla aynı."""
import _bootstrap  # noqa: F401
import os
import shutil
from pathlib import Path

from PIL import Image

import wiro_client
from themes.editorial_html_multi import build_html_multi, build_image_prompt

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates" / "menlo-ventures-carousel"
WIDTH, HEIGHT = 1080, 1350


def _placeholder(path):
    Image.new("RGB", (600, 600), (40, 40, 40)).save(path)


def _wiro_model():
    import yaml
    cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
    return cfg.get("wiro_model", "google/nano-banana-pro")


def _generate_photos(cards, outdir, model):
    """Her haber kartı için bir S/B foto üretir. -> {index: dosya_adı}.
    Bir `_news_{i}.png` zaten varsa yeniden kullanır (Wiro çağrısından kaçınır)."""
    paths = {}
    for i, card in enumerate(cards):
        subject = card.get("image_subject") or card.get("title") or "technology"
        dest = outdir / f"_news_{i}.png"
        if dest.exists():
            print(f"    · haber {i+1} fotoğrafı mevcut, yeniden kullanılıyor.")
            paths[i] = dest.name
            continue
        try:
            url = wiro_client.generate_image(
                build_image_prompt(subject), model=model, width=1024, height=1024,
            )
            wiro_client.download(url, dest)
        except Exception as ex:
            print(f"    ! Wiro haber {i+1} başarısız ({ex}); placeholder.")
            _placeholder(dest)
        paths[i] = dest.name
    return paths


def _generate_cover_photo(cover, outdir, model):
    """Kapak için Wiro S/B foto üretir -> dosya adı ('_cover.png').
    Varsa yeniden kullanır; hata halinde placeholder yazar."""
    dest = Path(outdir) / "_cover.png"
    if dest.exists():
        print("    · kapak fotoğrafı mevcut, yeniden kullanılıyor.")
        return dest.name
    subject = cover.get("image_subject") or cover.get("title") or "technology"
    try:
        url = wiro_client.generate_image(
            build_image_prompt(subject), model=model, width=1024, height=1024,
        )
        wiro_client.download(url, dest)
    except Exception as ex:
        print(f"    ! Wiro kapak başarısız ({ex}); placeholder.")
        _placeholder(dest)
    return dest.name


def render(cards, outdir, cover=None, cover_image_src=None):
    """N haber kartı + sabit CTA'yı editöryel temada render eder; sayaç toplamı = kart sayısı + 1.
    cover verilirse en başa 00 kapak kartı eklenir."""
    from playwright.sync_api import sync_playwright

    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # Önceki çalıştırmadan kalan bayat slaytları temizle
    for f in outdir.glob("slide_*.png"):
        f.unlink()

    for asset in ("logo-blue.svg", "cta-founders-investors-night.png"):
        shutil.copyfile(TEMPLATE_DIR / asset, outdir / asset)

    model = os.environ.get("WIRO_MODEL") or _wiro_model()
    cover_name = None
    if cover and cover_image_src:
        src = Path(cover_image_src)
        cover_name = "cover" + src.suffix.lower()
        if src.resolve() != (outdir / cover_name).resolve():
            shutil.copyfile(src, outdir / cover_name)
    elif cover:
        cover_name = _generate_cover_photo(cover, outdir, model)

    images = _generate_photos(cards, outdir, model)
    html = build_html_multi(cards, images, cover=cover, cover_image=cover_name)
    html_path = outdir / "_editorial_multi.html"
    html_path.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(
                viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=2,
            )
            page.goto(html_path.as_uri())
            page.wait_for_function("document.fonts.ready")
            page.wait_for_timeout(400)
            cards_el = page.query_selector_all("section.card")
            for idx, card in enumerate(cards_el, 1):
                card.screenshot(path=str(outdir / f"slide_{idx}.png"))
        finally:
            browser.close()

    for f in sorted(outdir.glob("slide_*.png")):
        with Image.open(f) as im:
            if im.size != (WIDTH, HEIGHT):
                im.resize((WIDTH, HEIGHT), Image.LANCZOS).save(f)

    return len(list(outdir.glob("slide_*.png")))
