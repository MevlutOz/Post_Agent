# themes/editorial.py
"""Editöryel tema — HTML şablonu → Wiro S/B fotoğrafları → Playwright PNG."""
import _bootstrap  # noqa: F401
import os
import shutil
from pathlib import Path

from PIL import Image

import wiro_client
from themes.editorial_html import build_html, build_image_prompt

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates" / "menlo-ventures-carousel"
WIDTH, HEIGHT = 1080, 1350


def photo_subjects(post):
    """Her foto slotu için Wiro konu metni (habere göre). PURE."""
    title = post.get("cover_title", "")
    slides = post.get("slides", [])

    def body(i):
        return slides[i]["body"] if i < len(slides) and slides[i].get("body") else title

    return {
        "hero": title or "modern technology and venture capital",
        "move": body(0),
        "founder": "a startup founder, portrait, workspace",
        "investor": "a venture capital investor in a boardroom",
    }


def _placeholder(path):
    Image.new("RGB", (600, 600), (40, 40, 40)).save(path)


def _generate_photos(post, outdir, model):
    subjects = photo_subjects(post)
    paths = {}
    for key, subject in subjects.items():
        dest = outdir / f"_img_{key}.png"
        try:
            url = wiro_client.generate_image(
                build_image_prompt(subject),
                model=model,
                width=1024,
                height=1024,
            )
            wiro_client.download(url, dest)
        except Exception as ex:
            print(f"    ! Wiro '{key}' başarısız ({ex}); placeholder kullanılıyor.")
            _placeholder(dest)
        paths[key] = dest.name  # HTML aynı klasörden çözecek
    return paths


def render(post, outdir):
    """posts.json post'unu editöryel temada 6 PNG olarak render eder."""
    from playwright.sync_api import sync_playwright

    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # Şablon varlıklarını çıktı klasörüne kopyala (HTML göreli yolla bulur)
    for asset in ("logo-blue.svg", "cta-founders-investors-night.png"):
        shutil.copyfile(TEMPLATE_DIR / asset, outdir / asset)

    images = _generate_photos(
        post, outdir, os.environ.get("WIRO_MODEL") or _wiro_model()
    )
    html = build_html(post, images)
    html_path = outdir / "_editorial.html"
    html_path.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=2,
        )
        page.goto(html_path.as_uri())
        page.wait_for_function("document.fonts.ready")
        page.wait_for_timeout(400)  # webfont boyama
        cards = page.query_selector_all("section.card")
        for idx, card in enumerate(cards, 1):
            card.screenshot(path=str(outdir / f"slide_{idx}.png"))
        browser.close()

    # device_scale_factor=2 → 2160×2700; 1080×1350'e indir
    for f in sorted(outdir.glob("slide_*.png")):
        with Image.open(f) as im:
            if im.size != (WIDTH, HEIGHT):
                im.resize((WIDTH, HEIGHT), Image.LANCZOS).save(f)

    return len(list(outdir.glob("slide_*.png")))


def _wiro_model():
    import yaml

    cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
    return cfg.get("wiro_model", "google/nano-banana-pro")
