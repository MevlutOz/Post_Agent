# themes/editorial_html_multi.py
"""5 haber + sabit CTA editöryel carousel'i için saf HTML üretimi.
Mevcut editorial_html.py tasarım diliyle aynı (Newsreader + Space Mono, mavi),
ama her kart AYRI bir haberdir ve kendi S/B fotoğrafını taşır."""
import html as _html

from themes.editorial_html import BLUE, _GRAIN, build_image_prompt  # noqa: F401

CORAL = "#FB6A5F"


def _e(s):
    return _html.escape(s or "")


def build_news_card(i, card, image_name, total=6):
    """Tek haber kartı (1..N) — 'yan yana' düzen. i: 1-tabanlı kart no. PURE."""
    kick = _e(card.get("kick", "")).upper()
    title = _e(card.get("title", ""))
    body = _e(card.get("body", ""))
    source = _e(card.get("source", ""))
    num = f"{i:02d}"
    return f"""<section data-screen-label="{num}" class="card"><div class="pad">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <img src="logo-blue.svg" alt="SaaSBridge" style="height:46px;"><span class="ctr">{num} / {total:02d}</span></div>
  <hr class="rule" style="margin-top:22px;">
  <div style="flex:1; display:flex; align-items:center; gap:48px;">
    <div style="flex:1; display:flex; flex-direction:column; gap:24px;">
      <span class="kick">{num} — {kick}</span>
      <h2 class="serif" style="margin:0; font-weight:800; font-size:60px; line-height:1.04; letter-spacing:-1.5px;">{title}</h2>
      <p class="serif" style="margin:0; font-size:32px; line-height:1.4; color:#2a2a2a;">{body}</p></div>
    <div class="imgwrap" style="width:392px; height:560px; box-shadow:-16px 16px 0 #0a0a0a;"><img src="{_e(image_name)}"></div>
  </div>
  <hr class="rule">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-top:18px;">
    <span class="cap">{source}</span><span class="cap" style="color:{BLUE};">@saasbridge</span></div>
</div><div class="grain"></div></section>"""


def build_cover_card(cover, image_name, total=6):
    """Kapak kartı (00) — başlık + altında tam genişlik foto bandı. PURE.
    accent varsa başlık iki katmanlı: üstte küçük siyah (title),
    altta büyük mavi (title_accent)."""
    kick = _e(cover.get("kick", ""))
    title = _e(cover.get("title", ""))
    accent = _e(cover.get("title_accent", ""))
    subtitle = _e(cover.get("subtitle", ""))
    footer = _e(cover.get("footer", "KAPAK DOSYASI"))
    if accent:
        title_html = (
            '<div style="display:flex; flex-direction:column; gap:8px;">'
            f'<span class="serif" style="font-weight:700; font-size:50px; line-height:1.03; letter-spacing:-1px; color:#0a0a0a;">{title}</span>'
            f'<span class="serif" style="font-weight:800; font-size:92px; line-height:0.98; letter-spacing:-2px; color:{BLUE};">{accent}</span>'
            '</div>'
        )
    else:
        title_html = f'<h1 class="serif" style="margin:0; font-weight:800; font-size:96px; line-height:0.98; letter-spacing:-2px;">{title}</h1>'
    tag_html = f'<span class="tag" style="align-self:flex-start;">{kick}</span>' if kick else ""
    return f"""<section data-screen-label="00" class="card"><div class="pad">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <img src="logo-blue.svg" alt="SaaSBridge" style="height:50px;"><span class="ctr">00 / {total:02d}</span></div>
  <hr class="rule" style="margin-top:22px;">
  <div style="flex:1; display:flex; flex-direction:column; justify-content:center; gap:24px;">
    {tag_html}
    {title_html}
    <p class="serif" style="margin:0; font-size:34px; line-height:1.4; color:#2a2a2a; max-width:900px;">{subtitle}</p>
    <div class="imgwrap" style="width:932px; height:390px; margin-top:8px;"><img src="{_e(image_name)}" style="object-position:center 28%; filter:grayscale(1) contrast(1.12);"></div>
  </div>
  <hr class="rule">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-top:18px;">
    <span class="cap">{footer}</span><span class="cap" style="color:{BLUE};">Kaydır →</span></div>
</div><div class="grain"></div></section>"""


def build_cta_card(total=6):
    """Son kart (CTA) — sabit Founders & Investors Night görseli. PURE."""
    return (f'<section data-screen-label="{total:02d}" class="card" style="background:#1b3dc0;">'
            '<img src="cta-founders-investors-night.png" alt="Founders &amp; Investors Night" '
            'style="display:block; width:1080px; height:1350px; object-fit:cover;"></section>')


def build_html_multi(cards, images, cover=None, cover_image=None):
    """cards: N haber sözlüğü. images: kart-index(0..N-1) -> dosya adı.
    Sayaç toplamı = haber sayısı + 1 (CTA). cover verilirse 00 kapak en başa. PURE."""
    total = len(cards) + 1
    news = "\n\n".join(
        build_news_card(i + 1, c, images.get(i, ""), total) for i, c in enumerate(cards)
    )
    cover_html = (build_cover_card(cover, cover_image or "", total) + "\n\n") if cover else ""
    cta_html = build_cta_card(total)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;0,6..72,700;0,6..72,800;1,6..72,600;1,6..72,700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#e7e7e3; }}
  .card {{ position:relative; width:1080px; height:1350px; overflow:hidden; background:#fff; color:#0a0a0a; }}
  .pad {{ position:absolute; inset:0; padding:74px; display:flex; flex-direction:column; }}
  .serif {{ font-family:'Newsreader',Georgia,serif; }}
  .kick {{ font-family:'Space Mono',monospace; text-transform:uppercase; letter-spacing:3px; font-size:22px; color:{BLUE}; }}
  .tag {{ font-family:'Space Mono',monospace; text-transform:uppercase; letter-spacing:2px; font-size:20px; background:#0a0a0a; color:#fff; padding:9px 16px; }}
  .ctr {{ font-family:'Space Mono',monospace; font-size:22px; letter-spacing:2px; color:#0a0a0a; }}
  .rule {{ height:1px; background:#e4e4df; border:0; margin:0; }}
  .cap {{ font-family:'Space Mono',monospace; text-transform:uppercase; letter-spacing:2px; font-size:18px; color:#6b6b6b; }}
  .grain {{ position:absolute; inset:0; background-image:url("{_GRAIN}"); background-size:300px; opacity:0.05; mix-blend-mode:multiply; pointer-events:none; z-index:8; }}
  .imgwrap {{ position:relative; overflow:hidden; border:2.5px solid #0a0a0a; box-shadow:16px 16px 0 #0a0a0a; }}
  .imgwrap img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; filter:grayscale(1) contrast(1.05); }}
</style></head><body>

{cover_html}{news}

{cta_html}

</body></html>"""
