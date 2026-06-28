"""CTA Mavi tema — posts.json'dan 1080x1350 carousel render eder (saf Pillow).
Eski make_image.py mantığı; tek fark: render(post, outdir) imzası."""
import _bootstrap  # noqa: F401  (.env + UTF-8)
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

# --- nihai boyut + supersample ---
S = 2                       # supersample (sonra nihai boyuta indirilir)
FW, FH = 1080, 1350         # WhatsApp CTA gibi dikey 4:5
W, H = FW * S, FH * S
def px(v): return int(round(v * S))

# --- WhatsApp temasından örneklenen renkler ---
PAPER     = (246, 245, 241)     # çerçeve / dash beyazı (pul kâğıdı)
BLUE_TOP  = (22, 66, 200)       # royal blue (üst)
BLUE_BOT  = (10, 36, 142)       # daha koyu (alt) -> hafif gradyan
INK       = (252, 251, 247)     # sıcak beyaz (başlık)
INK_SOFT  = (224, 228, 248)     # gövde için yumuşak beyaz
KICKER    = (176, 186, 232)     # kicker / footer soluk periwinkle
CORAL     = (250, 105, 100)     # mercan pill/vurgu  #FA6964
FADE_A    = 30                  # dekoratif soluk kelime alfa

KICKER_TEXT = "Haftalık Ekosistem Bülteni"   # kapak üst kicker (marka değil, tagline)

# --- font adayları (platformlar arası; ilk bulunan kullanılır) ---
_SERIF_BI = [   # zarif italik serif (başlıklar)
    r"C:\Windows\Fonts\georgiaz.ttf",          # Georgia Bold Italic (Windows)
    r"C:\Windows\Fonts\cambriaz.ttf",          # Cambria Bold Italic
    r"C:\Windows\Fonts\constanz.ttf",
    r"C:\Windows\Fonts\timesbi.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf",
]
_SANS = [       # düz sans (gövde / alt başlık)
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]
_SANS_B = [     # bold sans (kicker / footer / pill)
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]

def _font_path(cands):
    for p in cands:
        if Path(p).exists():
            return p
    return None

FS_PATH = _font_path(_SERIF_BI)
FR_PATH = _font_path(_SANS)
FB_PATH = _font_path(_SANS_B)

def font(path, size):
    if path:
        return ImageFont.truetype(path, px(size))
    return ImageFont.load_default()

# --- emoji/render edilemeyen karakterleri ayıkla (Arial/Georgia'da glyph yok) ---
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF"
    "\U0001F1E6-\U0001F1FF\U0000FE00-\U0000FE0F\U0000200D]+",
    flags=re.UNICODE,
)
def clean_text(t):
    if not t:
        return ""
    return re.sub(r"\s{2,}", " ", _EMOJI_RE.sub("", t)).strip()

def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()

def salient_words(title, n=2):
    words = re.findall(r"[0-9A-Za-zÇĞİıÖŞÜçğöşü']+", clean_text(title))
    words = [w for w in words if len(w) >= 4]
    words.sort(key=len, reverse=True)
    return [tr_upper(w) for w in words[:n]]

# ---------- beyaz logo ----------
def load_white_logo():
    cache = ROOT / "brand" / "saasbridge-logo-white.png"
    if cache.exists():
        return Image.open(cache).convert("RGBA")
    # asset yoksa SVG'den üretmeyi dene (svglib/reportlab/pycairo gerekir)
    svg = ROOT / "brand" / "saasbridge-logo.svg"
    if svg.exists():
        try:
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPM
            tmp = ROOT / "output" / "_logo_raw.png"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            renderPM.drawToFile(svg2rlg(str(svg)), str(tmp), fmt="PNG", dpi=600)
            raw = Image.open(tmp).convert("RGB"); pxs = raw.load()
            w, h = raw.size
            out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); op = out.load()
            for yy in range(h):
                for xx in range(w):
                    r, g, b = pxs[xx, yy]
                    a = 255 - min(r, g, b)
                    if a > 0:
                        op[xx, yy] = (255, 255, 255, a)
            out = out.crop(out.getbbox())
            out.save(cache); tmp.unlink(missing_ok=True)
            return out
        except Exception as ex:
            print(f"    ! Beyaz logo üretilemedi ({ex}); ikon PNG'ye düşülüyor.")
    fallback = ROOT / "brand" / "sb-icon-white@2x.png"
    return Image.open(fallback).convert("RGBA") if fallback.exists() else None

LOGO = load_white_logo()

# ---------- kesikli (dashed) çerçeve — WhatsApp CTA ile birebir ----------
def stamp_bg():
    grad = Image.new("RGB", (1, H)); gp = grad.load()
    for y in range(H):
        t = y / (H - 1)
        gp[0, y] = tuple(int(BLUE_TOP[i] + (BLUE_BOT[i] - BLUE_TOP[i]) * t) for i in range(3))
    img = grad.resize((W, H))
    d = ImageDraw.Draw(img)
    t  = px(13)        # çizgi kalınlığı (kenardan içe)
    cn = px(30)        # köşe çıkıntısı
    ut = px(60)        # hedef dash/boşluk birimi

    def segs(length):
        span = length - 2 * cn
        n = max(round((span / ut - 1) / 2), 1)
        u = span / (2 * n + 1)              # dash = boşluk = u (~60)
        out = [(0, cn)]
        pos = cn + u
        for _ in range(n):
            out.append((pos, u)); pos += 2 * u
        out.append((length - cn, cn))
        return out

    for a, ln in segs(W):                  # üst + alt
        d.rectangle([a, 0, a + ln, t], fill=PAPER)
        d.rectangle([a, H - t, a + ln, H], fill=PAPER)
    for a, ln in segs(H):                  # sol + sağ
        d.rectangle([0, a, t, a + ln], fill=PAPER)
        d.rectangle([W - t, a, W, a + ln], fill=PAPER)
    return img

# ---------- soluk dekoratif kelimeler (İŞİN / ZORU dizilimi) ----------
def draw_faded(img, words):
    if not words:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    f = font(FS_PATH, 158)
    big = words[0]
    bw = ld.textlength(big, font=f)
    ld.text((W - bw - px(48), H - px(322)), big, font=f, fill=(255, 255, 255, FADE_A))
    if len(words) > 1:
        ld.text((-px(34), px(118)), words[1], font=f, fill=(255, 255, 255, FADE_A))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

# ---------- metin yardımcıları ----------
def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in clean_text(text).split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            out.append(cur); cur = w
    if cur:
        out.append(cur)
    return out

def fit(d, text, path, maxw, start, mn, max_lines):
    size = start
    while size >= mn:
        f = font(path, size)
        lines = wrap(d, text, f, maxw)
        if len(lines) <= max_lines and all(d.textlength(l, font=f) <= maxw for l in lines):
            return f, lines, size
        size -= 2
    f = font(path, mn)
    return f, wrap(d, text, f, maxw), mn

def center_lines(d, lines, f, y, fill, lh):
    for l in lines:
        w = d.textlength(l, font=f)
        d.text(((W - w) / 2, y), l, font=f, fill=fill)
        y += lh
    return y

def coral_bar(d, y):
    bw, bh = px(96), px(9)
    d.rounded_rectangle([(W - bw) / 2, y, (W + bw) / 2, y + bh], radius=bh / 2, fill=CORAL)
    return y + bh

def coral_pill(d, text, cy):
    text = clean_text(text)
    f = font(FB_PATH, 33)
    tw = d.textlength(text, font=f)
    pw, ph = tw + px(92), px(76)
    x0 = (W - pw) / 2
    d.rounded_rectangle([x0, cy, x0 + pw, cy + ph], radius=ph / 2, fill=CORAL)
    d.text((W / 2, cy + ph / 2), text, font=f, fill=(255, 255, 255), anchor="mm")
    return cy + ph

def footer(d, source):
    f = font(FB_PATH, 23)
    txt = tr_upper(f"Kaynak · {clean_text(source)}")
    w = d.textlength(txt, font=f)
    d.text(((W - w) / 2, H - px(86)), txt, font=f, fill=KICKER)

# ---------- slayt çizimleri ----------
def render_cover(post):
    img = draw_faded(stamp_bg(), salient_words(post["cover_title"]))
    d = ImageDraw.Draw(img)
    if LOGO is not None:
        lh = px(88); lw = int(LOGO.width * lh / LOGO.height)
        logo = LOGO.resize((lw, lh), Image.LANCZOS)
        img.paste(logo, (int((W - lw) / 2), px(150)), logo)
    fk = font(FB_PATH, 24)
    kick = tr_upper(KICKER_TEXT)
    kw = d.textlength(kick, font=fk)
    d.text(((W - kw) / 2, px(276)), kick, font=fk, fill=KICKER)
    f, lines, sz = fit(d, post["cover_title"], FS_PATH, W - px(170), 100, 60, 3)
    lh2 = px(int(sz * 1.16)); block_h = lh2 * len(lines)
    y0 = int(H * 0.44) - block_h // 2
    y_end = center_lines(d, lines, f, y0, INK, lh2)
    yb = coral_bar(d, y_end + px(30))
    fs = font(FR_PATH, 37)
    sub = wrap(d, post.get("cover_subtitle", ""), fs, W - px(230))
    center_lines(d, sub, fs, yb + px(44), INK_SOFT, px(52))
    footer(d, post["source"])
    return img

def render_detail(sl, source):
    img = draw_faded(stamp_bg(), salient_words(sl["heading"]))
    d = ImageDraw.Draw(img)
    fh, hlines, hsz = fit(d, sl["heading"], FS_PATH, W - px(150), 88, 54, 2)
    hlh = px(int(hsz * 1.16))
    fb = font(FR_PATH, 37)
    blines = wrap(d, sl.get("body", ""), fb, W - px(190))
    blh = px(52)
    total = hlh * len(hlines) + px(85) + blh * len(blines)
    y = (H - total) // 2 - px(20)
    y = center_lines(d, hlines, fh, y, INK, hlh)
    yb = coral_bar(d, y + px(30))
    center_lines(d, blines, fb, yb + px(46), INK_SOFT, blh)
    footer(d, source)
    return img

def render_cta(post):
    img = draw_faded(stamp_bg(), salient_words(post["cta_title"]))
    d = ImageDraw.Draw(img)
    f, lines, sz = fit(d, post["cta_title"], FS_PATH, W - px(160), 90, 56, 3)
    lh = px(int(sz * 1.16)); block_h = lh * len(lines)
    y0 = int(H * 0.40) - block_h // 2
    y_end = center_lines(d, lines, f, y0, INK, lh)
    yb = coral_bar(d, y_end + px(30))
    sub = post.get("cta_subtitle", "Takip et: @saasbridge")
    coral_pill(d, sub, yb + px(54))
    footer(d, post["source"])
    return img

def build_slides(post):
    slides = [("cover", post)]
    for s in post.get("slides", []):
        slides.append(("detail", s))
    slides.append(("cta", post))
    return slides


def render(post, outdir):
    """posts.json post'unu CTA Mavi temada outdir'e slide_*.png olarak render eder.
    Üretilen slayt sayısını döndürür."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    src = post["source"]
    slides = build_slides(post)
    for idx, (kind, data) in enumerate(slides, 1):
        if kind == "cover":
            img = render_cover(post)
        elif kind == "cta":
            img = render_cta(post)
        else:
            img = render_detail(data, src)
        img.resize((FW, FH), Image.LANCZOS).save(outdir / f"slide_{idx}.png")
    return len(slides)
