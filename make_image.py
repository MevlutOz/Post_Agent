"""
make_image.py — Her post için 1080x1080 Instagram görsel kartı üretir.

İki mod:
  • Wiro AI varsa (WIRO_API_KEY): Wiro üretken arka plan görseli üretir,
    üstüne karartma + marka + başlık basılır (zengin + okunabilir).
  • Wiro yoksa: düz koyu marka şablonu (her zaman çalışır).

Çıktı: output/<tarih>/post_N.png
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import json, os
from pathlib import Path
from datetime import date
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).parent
posts = json.loads((ROOT / "data" / "posts.json").read_text(encoding="utf-8"))
today = date.today().isoformat()
outdir = ROOT / "output" / today
outdir.mkdir(parents=True, exist_ok=True)

# --- Marka paleti (SaaS Bridge marka kimliği) ---
# Palet: #2928B6 (koyu indigo), #4341D1 (royal blue), #8B8AE8 (periwinkle)
BRAND_DEEP   = (41, 40, 182)    # #2928B6
BRAND_ROYAL  = (67, 65, 209)    # #4341D1
BRAND_LIGHT  = (139, 138, 232)  # #8B8AE8
BG      = (13, 12, 35)          # koyu indigo zemin (markaya uyumlu)
ACCENT  = BRAND_LIGHT           # vurgu: periwinkle (koyu zeminde okunur)
WHITE   = (245, 247, 252)
MUTED   = (165, 168, 210)       # soluk periwinkle
W = H = 1080

# Marka logosu (koyu zemin için beyaz ikon)
LOGO_PATH = ROOT / "brand" / "sb-icon-white@2x.png"

USE_WIRO = bool(os.environ.get("WIRO_API_KEY"))
WIRO_MODEL = None
if USE_WIRO:
    import wiro_client, yaml
    _cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
    WIRO_MODEL = os.environ.get("WIRO_MODEL") or _cfg.get("wiro_model")

# Platformlar arası font adayları (ilk bulunan kullanılır)
_FONTS_BOLD = [
    r"C:\Windows\Fonts\arialbd.ttf",                                   # Windows
    r"C:\Windows\Fonts\segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",            # Linux
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",              # macOS
]
_FONTS_REG = [
    r"C:\Windows\Fonts\arial.ttf",                                     # Windows
    r"C:\Windows\Fonts\segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",                 # Linux
    "/System/Library/Fonts/Supplemental/Arial.ttf",                  # macOS
]

def load_font(size, bold=False):
    for p in (_FONTS_BOLD if bold else _FONTS_REG):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

f_title = load_font(72, bold=True)
f_sub   = load_font(38)
f_brand = load_font(34, bold=True)
f_foot  = load_font(26)

def load_logo(height):
    """Marka ikonunu verilen yükseklikte (oranı koruyarak) yükler."""
    if LOGO_PATH.exists():
        lg = Image.open(LOGO_PATH).convert("RGBA")
        w = int(lg.width * height / lg.height)
        return lg.resize((w, height))
    return None

LOGO = load_logo(64)

def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def wiro_background(post, idx):
    """Wiro'dan habere uygun, metinsiz, atmosferik bir arka plan üretir."""
    prompt = (
        f"Abstract modern tech editorial background for a SaaS/AI news card. "
        f"Theme: {post['visual_title']}. "
        f"Deep indigo and royal blue base (hex #2928B6 and #4341D1), "
        f"soft periwinkle blue accents (hex #8B8AE8), soft gradient, depth, "
        f"minimal geometric shapes, premium startup aesthetic, "
        f"strictly blue/indigo color palette, no teal, no green, "
        f"no text, no words, no letters, "
        f"clean negative space on the left half for overlaid text."
    )
    try:
        url = wiro_client.generate_image(prompt, model=WIRO_MODEL, width=1080, height=1080)
        raw = outdir / f"_bg_{idx}.png"
        wiro_client.download(url, raw)
        img = Image.open(raw).convert("RGB").resize((W, H))
        return img
    except Exception as ex:
        print(f"    ! Wiro arka plan başarısız ({ex}); düz zemine düşülüyor.")
        return None

for i, p in enumerate(posts, 1):
    bg = wiro_background(p, i) if USE_WIRO else None
    if bg is None:
        img = Image.new("RGB", (W, H), BG)
    else:
        img = bg
        # okunabilirlik: sol-alt karartma katmanı (gradient yerine düz overlay)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rectangle([0, 0, W, H], fill=(10, 12, 20, 130))      # genel karartma
        od.rectangle([0, 260, W, H], fill=(10, 12, 20, 90))     # alt yarı ekstra
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    d = ImageDraw.Draw(img)
    margin = 90

    d.rectangle([0, 0, W, 12], fill=ACCENT)                     # üst accent
    d.rectangle([margin, 300, margin + 70, 312], fill=ACCENT)   # başlık çizgisi

    # marka logosu + isim (üst sol)
    bx = margin
    if LOGO is not None:
        img.paste(LOGO, (margin, 56), LOGO)
        bx = margin + LOGO.width + 24
    d.text((bx, 62), "SAAS BRIDGE", font=f_brand, fill=WHITE)
    d.text((bx, 104), "Haftalık Ekosistem Bülteni", font=f_foot, fill=MUTED)

    y = 340
    for line in wrap(d, p["visual_title"], f_title, W - 2 * margin):
        d.text((margin, y), line, font=f_title, fill=WHITE)
        y += 86

    y += 24
    for line in wrap(d, p["visual_subtitle"], f_sub, W - 2 * margin):
        d.text((margin, y), line, font=f_sub, fill=MUTED)
        y += 50

    d.line([margin, H - 130, W - margin, H - 130], fill=(60, 70, 90), width=2)
    d.text((margin, H - 100), f"Kaynak: {p['source']}", font=f_foot, fill=MUTED)
    d.text((margin, H - 64), "@saasbridge", font=f_foot, fill=ACCENT)

    path = outdir / f"post_{i}.png"
    img.save(path)
    # geçici bg dosyasını temizle
    bgfile = outdir / f"_bg_{i}.png"
    if bgfile.exists(): bgfile.unlink()
    print(f"  ✓ {path.name}" + ("  (Wiro arka plan)" if bg is not None else "  (düz şablon)"))

print(f"\nGörseller hazır: output/{today}/")
