# themes/editorial_html.py
"""Editöryel tema için saf HTML üretimi (Playwright bunu render eder).
MenloVenturesCarousel.dc.html tasarımından uyarlanmıştır."""
import html as _html
import re

BLUE = "#0050EE"

# Grain: eksik grain.png yerine gömülü SVG feTurbulence data-URI.
_GRAIN = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'>"
    "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' "
    "numOctaves='2'/></filter><rect width='100%25' height='100%25' "
    "filter='url(%23n)' opacity='1'/></svg>"
)


def color_last_clause(title):
    title = title or ""
    m = re.search(r"[,.]\s*", title)
    if not m:
        return _html.escape(title)
    head = title[: m.end()]
    tail = title[m.end():]
    if not tail.strip():
        return _html.escape(title)
    return (f"{_html.escape(head)}"
            f"<span style=\"color:{BLUE};\">{_html.escape(tail)}</span>")


def build_image_prompt(subject):
    return (
        f"High-contrast black and white editorial documentary photograph about "
        f"{subject}. Photojournalism, dramatic lighting, grain, premium magazine "
        f"aesthetic. No text, no words, no letters, no watermark, no logo."
    )


def card_payload(post):
    slides = list(post.get("slides", []))
    while len(slides) < 3:
        slides.append({"heading": "", "body": ""})
    return {
        "cover_title": post.get("cover_title", ""),
        "cover_subtitle": post.get("cover_subtitle", ""),
        "slides": [{"heading": s.get("heading", ""), "body": s.get("body", "")}
                   for s in slides[:3]],
        "cta_title": post.get("cta_title", ""),
        "source": post.get("source", ""),
    }


def _e(s):
    return _html.escape(s or "")


def build_html(post, images):
    cp = card_payload(post)
    s0, s1, s2 = cp["slides"]
    src = _e(cp["source"])
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

<section data-screen-label="01" class="card"><div class="pad">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <img src="logo-blue.svg" alt="SaaSBridge" style="height:50px;">
    <span class="ctr">01 / 06</span></div>
  <hr class="rule" style="margin-top:22px;">
  <div style="flex:1; display:flex; flex-direction:column; justify-content:center; gap:30px;">
    <span class="tag" style="align-self:flex-start;">Büyük Hikâye · SaaS &amp; AI</span>
    <h1 class="serif" style="margin:0; font-weight:800; font-size:104px; line-height:0.98; letter-spacing:-2px;">{color_last_clause(cp['cover_title'])}</h1>
    <p class="serif" style="margin:0; font-size:36px; line-height:1.4; color:#2a2a2a; max-width:840px;">{_e(cp['cover_subtitle'])}</p>
    <div class="imgwrap" style="width:932px; height:380px; margin-top:6px;"><img src="{_e(images['hero'])}"></div>
    <span class="cap">{src}</span>
  </div>
  <hr class="rule">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-top:18px;">
    <span class="cap">Yatırım Dersi · 1/6</span><span class="cap" style="color:{BLUE};">Kaydır →</span></div>
</div><div class="grain"></div></section>

<section data-screen-label="02" class="card"><div class="pad">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <img src="logo-blue.svg" alt="SaaSBridge" style="height:46px;"><span class="ctr">02 / 06</span></div>
  <hr class="rule" style="margin-top:22px;">
  <div style="flex:1; display:flex; align-items:center; gap:48px;">
    <div style="flex:1; display:flex; flex-direction:column; gap:26px;">
      <span class="kick">01 — {_e(s0['heading'])}</span>
      <p class="serif" style="margin:0; font-size:38px; line-height:1.4; color:#2a2a2a;">{_e(s0['body'])}</p></div>
    <div class="imgwrap" style="width:360px; height:500px; box-shadow:-16px 16px 0 #0a0a0a;"><img src="{_e(images['move'])}"></div>
  </div>
  <hr class="rule">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-top:18px;">
    <span class="cap">{src}</span><span class="cap">@saasbridge</span></div>
</div><div class="grain"></div></section>

<section data-screen-label="03" class="card"><div class="pad">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <img src="logo-blue.svg" alt="SaaSBridge" style="height:46px;"><span class="ctr">03 / 06</span></div>
  <hr class="rule" style="margin-top:22px;">
  <div style="flex:1; display:flex; flex-direction:column; justify-content:center; gap:14px;">
    <span class="kick" style="margin-bottom:10px;">02 — {_e(s1['heading'])}</span>
    <div class="serif" style="font-weight:800; font-size:150px; line-height:0.5; color:#FB6A5F;">“</div>
    <h2 class="serif" style="margin:0; font-weight:700; font-style:italic; font-size:68px; line-height:1.08; letter-spacing:-1.5px;">{_e(s1['body'])}</h2>
  </div>
  <hr class="rule">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-top:18px;">
    <span class="cap">Çıkarım</span><span class="cap">@saasbridge</span></div>
</div><div class="grain"></div></section>

<section data-screen-label="04" class="card"><div class="pad">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <img src="logo-blue.svg" alt="SaaSBridge" style="height:46px;"><span class="ctr">04 / 06</span></div>
  <hr class="rule" style="margin-top:22px;">
  <div style="flex:1; display:flex; flex-direction:column; justify-content:center; gap:34px;">
    <span class="kick">03 — {_e(s2['heading'])}</span>
    <div style="display:flex; gap:40px;">
      <div class="imgwrap" style="flex:1; height:430px;"><img src="{_e(images['founder'])}"></div>
      <div class="imgwrap" style="flex:1; height:430px;"><img src="{_e(images['investor'])}"></div>
    </div>
    <p class="serif" style="margin:0; font-size:34px; line-height:1.4; color:#2a2a2a;">{_e(s2['body'])}</p>
  </div>
  <hr class="rule">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-top:18px;">
    <span class="cap">{src}</span><span class="cap">@saasbridge</span></div>
</div><div class="grain"></div></section>

<section data-screen-label="05" class="card"><div class="pad">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <img src="logo-blue.svg" alt="SaaSBridge" style="height:46px;"><span class="ctr">05 / 06</span></div>
  <hr class="rule" style="margin-top:22px;">
  <div style="flex:1; display:flex; flex-direction:column; justify-content:center; gap:30px;">
    <span class="kick">Peki ya sen?</span>
    <h2 class="serif" style="margin:0; font-weight:800; font-size:84px; line-height:1.0; letter-spacing:-2px;">{_e(cp['cta_title'])}</h2>
    <span style="align-self:flex-start; margin-top:8px; display:inline-flex; align-items:center; gap:14px; padding:20px 34px; background:{BLUE}; color:#fff; font-family:'Space Mono',monospace; font-size:26px; letter-spacing:1px;">YORUMLARDA BULUŞALIM <span style="font-size:28px;">→</span></span>
  </div>
  <hr class="rule">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-top:18px;">
    <span class="cap">Tartışmaya katıl</span><span class="cap" style="color:{BLUE};">@saasbridge</span></div>
</div><div class="grain"></div></section>

<section data-screen-label="06" class="card" style="background:#1b3dc0;">
  <img src="cta-founders-investors-night.png" alt="Founders &amp; Investors Night" style="display:block; width:1080px; height:1350px; object-fit:cover;">
</section>

</body></html>"""
