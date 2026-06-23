# Carousel Post + İnteraktif Haber Seçimi — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pipeline'ı, otomatik 3 post yerine kullanıcıya detaylı haber listesi sunup tek haber seçtiren ve seçilen haberi 5 slaytlık kaydırmalı (carousel) Instagram postuna dönüştüren bir akışa çevir.

**Architecture:** `fetch → curate (aday listesi anotasyonu) → select (terminalde tek seçim) → generate (carousel JSON) → make_image (N slayt PNG)`. Adımlar `run.py` tarafından sırayla `subprocess` ile çağrılır; 3. adım kullanıcı girdisi bekler (stdin devralınır). Windows zamanlanmış görevi kaldırılır.

**Tech Stack:** Python 3.12, `anthropic` (Claude Opus 4.8), `feedparser`, `PyYAML`, `Pillow`, `python-dotenv`, Wiro AI (opsiyonel görsel), test için `pytest`.

## Global Constraints

- Dil: tüm kullanıcıya görünen metin ve caption Türkçe.
- Marka paleti (verbatim): `#2928B6` (deep indigo) / `#4341D1` (royal blue) / `#8B8AE8` (periwinkle); koyu indigo zemin `(13, 12, 35)`. Teal/yeşil YOK.
- Her step script'i ilk satırda `import _bootstrap` yapar (.env + UTF-8 stdout).
- Claude modeli: `claude-opus-4-8`.
- Proje git deposu DEĞİL → plandaki "Kontrol Noktası" adımları `git commit` yerine geçer. (İstenirse önce `git init` yapılabilir; zorunlu değil.)
- Carousel toplam slayt = 1 kapak + N detay + 1 CTA; N = `sources.yaml > settings.carousel_detail_slides` (varsayılan 3).
- Çıktı klasörü: `output/<YYYY-MM-DD>/` → `slide_1.png … slide_<toplam>.png` + `captions.md`.

---

### Task 1: `select.py` girdi ayrıştırma (pure logic + TDD)

İlk olarak saf, test edilebilir `parse_choice` fonksiyonunu yaz. `select.py`'nin geri kalanı (I/O) Task 2'de eklenir; bu task yalnızca ayrıştırma mantığını ve testini kapsar.

**Files:**
- Create: `select.py`
- Create: `tests/test_select.py`
- Create: `tests/__init__.py` (boş)

**Interfaces:**
- Produces: `parse_choice(raw: str, n: int) -> int | None` — geçerli girdide 0-tabanlı indeks (1..n → 0..n-1), geçersizde `None`.

- [ ] **Step 1: pytest kurulu mu kontrol et, değilse kur**

Run: `python -m pytest --version`
Beklenen: sürüm yazısı. Hata verirse: `python -m pip install pytest` çalıştır.

- [ ] **Step 2: Başarısız testi yaz**

`tests/__init__.py` → boş dosya oluştur.

`tests/test_select.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from select import parse_choice


def test_valid_choice_returns_zero_based_index():
    assert parse_choice("1", 15) == 0
    assert parse_choice("15", 15) == 14


def test_strips_whitespace():
    assert parse_choice("  3  ", 15) == 2


def test_empty_returns_none():
    assert parse_choice("", 15) is None
    assert parse_choice("   ", 15) is None


def test_non_digit_returns_none():
    assert parse_choice("abc", 15) is None
    assert parse_choice("2x", 15) is None


def test_out_of_range_returns_none():
    assert parse_choice("0", 15) is None
    assert parse_choice("16", 15) is None
    assert parse_choice("-1", 15) is None
```

- [ ] **Step 3: Testi çalıştır, başarısız olduğunu doğrula**

Run: `python -m pytest tests/test_select.py -v`
Beklenen: FAIL — `ImportError`/`ModuleNotFoundError` (select.py veya parse_choice yok).

- [ ] **Step 4: `parse_choice`'u yaz**

`select.py` (şimdilik sadece fonksiyon + bootstrap; I/O Task 2'de):
```python
"""
select.py — Adayları terminalde listeler, kullanıcıdan TEK haber seçtirir.
Çıktı: data/curated.json (tek elemanlı liste)
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import json
from pathlib import Path

ROOT = Path(__file__).parent


def parse_choice(raw, n):
    """'1'..'n' arası geçerli girdiyi 0-tabanlı indekse çevirir, yoksa None."""
    raw = (raw or "").strip()
    if not raw.lstrip("-").isdigit():
        return None
    v = int(raw)
    if 1 <= v <= n:
        return v - 1
    return None
```
Not: `import _bootstrap` test ortamında da import edilir; `_bootstrap` hata yutar, sorun olmaz.

- [ ] **Step 5: Testi çalıştır, geçtiğini doğrula**

Run: `python -m pytest tests/test_select.py -v`
Beklenen: 5 test PASS.

- [ ] **Step 6: Kontrol Noktası**

`python -m pytest tests/test_select.py -v` çıktısında tüm testlerin PASS olduğunu gözle doğrula. (Git yoksa commit yerine bu doğrulama yeterli.)

---

### Task 2: `select.py` interaktif liste + seçim (I/O)

`parse_choice`'u kullanarak adayları detaylı listeleyen ve seçilen haberi yazan I/O kısmını tamamla.

**Files:**
- Modify: `select.py` (Task 1'de oluşturuldu, sonuna I/O eklenir)

**Interfaces:**
- Consumes: `data/candidates.json` (Task 3'te curate.py üretir) — liste; her öğe `{title, source, summary, link, reason, angle}`.
- Consumes: `parse_choice` (Task 1).
- Produces: `data/curated.json` — tek elemanlı liste, seçilen aday öğesinin aynısı.

- [ ] **Step 1: Liste + seçim mantığını `select.py` sonuna ekle**

`select.py` sonuna ekle:
```python
def format_candidate(i, c):
    """Tek adayı numaralı, detaylı blok olarak biçimler."""
    summary = (c.get("summary") or "").strip()
    if len(summary) > 220:
        summary = summary[:220].rstrip() + "…"
    lines = [
        f"{i}) [{c.get('source','?')}] {c.get('title','').strip()}",
    ]
    if summary:
        lines.append(f"     Özet: {summary}")
    if c.get("reason"):
        lines.append(f"     Neden ilgi çekici: {c['reason']}")
    if c.get("angle"):
        lines.append(f"     Önerilen açı: {c['angle']}")
    return "\n".join(lines)


def main():
    cand_path = ROOT / "data" / "candidates.json"
    if not cand_path.exists():
        print("✗ data/candidates.json yok. Önce curate.py çalıştırılmalı.")
        raise SystemExit(1)

    candidates = json.loads(cand_path.read_text(encoding="utf-8"))
    if not candidates:
        print("✗ Aday haber listesi boş. fetch/curate adımlarını kontrol et.")
        raise SystemExit(1)

    n = len(candidates)
    print("\n" + "=" * 60)
    print("  Bu haftanın haber adayları")
    print("=" * 60)
    for i, c in enumerate(candidates, 1):
        print()
        print(format_candidate(i, c))
    print()

    while True:
        raw = input(f"Hangi haberi post yapalım? (1-{n}): ")
        idx = parse_choice(raw, n)
        if idx is not None:
            break
        print(f"  ! Geçersiz giriş. 1 ile {n} arasında bir numara gir.")

    chosen = candidates[idx]
    (ROOT / "data" / "curated.json").write_text(
        json.dumps([chosen], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✓ Seçildi: {chosen.get('title','')[:70]}")
    print("  → data/curated.json yazıldı.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Sahte candidates.json ile elle doğrula**

Geçici test verisi oluştur ve çalıştır:
```bash
python -c "import json,os; os.makedirs('data',exist_ok=True); json.dump([{'title':'Test Haber A','source':'X','summary':'ozet a','link':'http://a','reason':'r1','angle':'a1'},{'title':'Test Haber B','source':'Y','summary':'ozet b','link':'http://b','reason':'r2','angle':'a2'}], open('data/candidates.json','w',encoding='utf-8'), ensure_ascii=False)"
echo 2 | python select.py
```
Beklenen: iki aday detaylı listelenir; `✓ Seçildi: Test Haber B` yazılır; `data/curated.json` tek elemanlı liste (B) içerir.

- [ ] **Step 3: curated.json içeriğini doğrula**

Run: `python -c "import json; d=json.load(open('data/curated.json',encoding='utf-8')); print(len(d), d[0]['title'])"`
Beklenen: `1 Test Haber B`

- [ ] **Step 4: Geçersiz girdi tekrar sorgusunu doğrula**

Run: `printf '0\nabc\n1\n' | python select.py`
Beklenen: iki kez "Geçersiz giriş" uyarısı, sonra `✓ Seçildi: Test Haber A`.

- [ ] **Step 5: Kontrol Noktası**

Step 2-4 çıktılarının beklenenle eşleştiğini gözle doğrula.

---

### Task 3: `curate.py` — otomatik seçim yerine aday anotasyonu

Claude'un 3 haber seçmesini, en alakalı ~15 haberi sıralayıp her birine `reason` + `angle` ekleyen anotasyona çevir.

**Files:**
- Modify: `curate.py` (tamamı yeniden yazılır)

**Interfaces:**
- Consumes: `data/articles_raw.json` (fetch.py), `sources.yaml`.
- Produces: `data/candidates.json` — liste; her öğe `{source, title, link, summary, date, reason, angle}`.

- [ ] **Step 1: `curate.py`'yi yeniden yaz**

`curate.py` tam içerik:
```python
"""
curate.py — Claude API: toplanan haberlerden en alakalı ~N adayı seçip
sıralar ve her birine kısa 'neden ilgi çekici' + 'önerilen açı' ekler.
Otomatik post ÜRETMEZ; sadece kullanıcıya sunulacak aday listesini hazırlar.
Çıktı: data/candidates.json
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import json, yaml
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).parent
cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
client = Anthropic()  # ANTHROPIC_API_KEY ortam değişkeninden okunur

articles = json.loads((ROOT / "data" / "articles_raw.json").read_text(encoding="utf-8"))
articles = articles[: cfg["settings"]["max_articles_to_claude"]]

max_candidates = cfg["settings"].get("max_candidates", 15)
brand = cfg["settings"]["brand_name"]

listing = "\n".join(
    f"[{i}] ({a['source']}) {a['title']} — {a['summary'][:200]}"
    for i, a in enumerate(articles)
)

prompt = f"""Sen {brand} adlı, Türkiye SaaS & AI ekosistemine odaklanan bir
topluluğun içerik editörüsün. Aşağıda son 1 haftanın haber başlıkları var.

Hedef kitle: kurucular, yatırımcılar, SaaS/AI girişimcileri.
Konular: SaaS, AI, AI agent, girişimcilik, yatırım/VC.

Görevin: Bu listeden Instagram'da paylaşmaya EN değer en fazla {max_candidates}
haberi seç ve EN ilgi çekiciden aza doğru SIRALA. Magazinsel/alakasız olanları ele.
Kriterler: güncellik, ekosisteme alaka, kurucuların ilgisini çekme, özgünlük.

SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{{
  "candidates": [
    {{"index": <haber no>, "reason": "<neden ilgi çekici, 1 cümle TR>", "angle": "<post için açı/vurgu, 1 cümle TR>"}}
  ]
}}

Haberler:
{listing}
"""

resp = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=2500,
    messages=[{"role": "user", "content": prompt}],
)
text = resp.content[0].text.strip()
text = text.replace("```json", "").replace("```", "").strip()
sel = json.loads(text)["candidates"]

candidates = []
for s in sel:
    i = s["index"]
    if not (0 <= i < len(articles)):
        continue
    art = articles[i]
    candidates.append({**art, "reason": s["reason"], "angle": s["angle"]})

(ROOT / "data" / "candidates.json").write_text(
    json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"{len(candidates)} aday haber hazırlandı:")
for i, c in enumerate(candidates, 1):
    print(f"  {i}. {c['title'][:70]}")
```

- [ ] **Step 2: Çalıştır (gerçek Claude çağrısı, .env dolu olmalı)**

Run: `python fetch.py && python curate.py`
Beklenen: "N aday haber hazırlandı:" + numaralı başlık listesi; N ≤ 15.

- [ ] **Step 3: Çıktı şemasını doğrula**

Run: `python -c "import json; d=json.load(open('data/candidates.json',encoding='utf-8')); a=d[0]; print(len(d)); print(all(k in a for k in ('title','source','summary','link','reason','angle')))"`
Beklenen: aday sayısı + `True`.

- [ ] **Step 4: Kontrol Noktası**

candidates.json'un sıralı ve her öğenin reason/angle içerdiğini gözle doğrula.

---

### Task 4: `generate.py` — seçilen haber için carousel JSON

Tek seçilen haberi (curated.json) carousel yapısına dönüştür: kapak + N detay slaytı + CTA + IG caption.

**Files:**
- Modify: `generate.py` (tamamı yeniden yazılır)

**Interfaces:**
- Consumes: `data/curated.json` (Task 2, tek elemanlı liste), `sources.yaml`.
- Produces: `data/posts.json` — tek nesne `{cover_title, cover_subtitle, slides:[{heading,body}], cta_title, cta_subtitle, caption, hashtags, source, link}`; `output/<tarih>/captions.md`.

- [ ] **Step 1: `generate.py`'yi yeniden yaz**

`generate.py` tam içerik:
```python
"""
generate.py — Claude API: seçilen TEK haberi kaydırmalı (carousel) Instagram
postuna dönüştürür: kapak + N detay slaytı + CTA + IG caption/hashtag.
Çıktı: data/posts.json + output/<tarih>/captions.md
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import json, yaml
from pathlib import Path
from datetime import date
from anthropic import Anthropic

ROOT = Path(__file__).parent
cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
client = Anthropic()
brand = cfg["settings"]["brand_name"]

DETAIL_HEADINGS = ["Ne oldu?", "Neden önemli?", "Kuruculara ne anlama geliyor?"]
n_detail = cfg["settings"].get("carousel_detail_slides", 3)
headings = DETAIL_HEADINGS[:n_detail]

curated = json.loads((ROOT / "data" / "curated.json").read_text(encoding="utf-8"))
c = curated[0]

headings_block = "\n".join(f"- {h}" for h in headings)
prompt = f"""Sen {brand} topluluğunun Instagram içerik yazarısın.
Marka tonu: bilgili ama samimi, kurucu-dostu, abartısız, Türkçe.
Hedef kitle: Türkiye'deki SaaS/AI kurucuları ve yatırımcılar.

Aşağıdaki haberi KAYDIRMALI (carousel) bir Instagram postuna dönüştür.
Post yapısı: 1 kapak slaytı + şu detay slaytları + 1 kapanış (CTA) slaytı.

Detay slaytı başlıkları (bu sırayla, aynı başlıkları kullan):
{headings_block}

Haber başlığı: {c['title']}
Kaynak: {c['source']}
Özet: {c['summary']}
Önerilen açı: {c['angle']}

SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{{
  "cover_title": "<kapak için çarpıcı kısa başlık, max 8 kelime, TR>",
  "cover_subtitle": "<kapak alt satırı, 1 kısa cümle, TR>",
  "slides": [
    {{"heading": "<yukarıdaki başlıklardan biri, sırayla>", "body": "<2-3 kısa cümle, TR; o slaytın içeriği>"}}
  ],
  "cta_title": "<kapanış slaytı: etkileşime davet eden kısa soru, TR>",
  "caption": "<Instagram açıklaması: 2-3 paragraf. Haberi özetle, kurucuya 'ne anlama geliyor' bağla, sonunda soruyla etkileşime davet et. Emoji ölçülü>",
  "hashtags": ["#saas", "#yapayzeka"]
}}
"slides" dizisi tam {len(headings)} öğe içermeli ve başlıklar verilen sırayla olmalı.
"""

resp = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}],
)
text = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
data = json.loads(text)

# Slayt başlıklarını güvenceye al (Claude sırayı/başlığı kaçırırsa düzelt)
slides = data.get("slides", [])
for i, h in enumerate(headings):
    if i < len(slides):
        slides[i]["heading"] = h
    else:
        slides.append({"heading": h, "body": ""})
data["slides"] = slides[: len(headings)]

data["cta_subtitle"] = "Takip et: @saasbridge"
data["source"] = c["source"]
data["link"] = c["link"]

(ROOT / "data" / "posts.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
)

today = date.today().isoformat()
outdir = ROOT / "output" / today
outdir.mkdir(parents=True, exist_ok=True)
md = [f"# {brand} — Instagram Carousel ({today})\n"]
md.append(f"## Kapak: {data['cover_title']}\n")
md.append(f"**Alt başlık:** {data['cover_subtitle']}\n")
for i, s in enumerate(data["slides"], 2):
    md.append(f"### Slayt {i}: {s['heading']}\n\n{s['body']}\n")
md.append(f"### Son slayt (CTA): {data['cta_title']}\n\n{data['cta_subtitle']}\n")
md.append(f"\n**Kaynak:** {data['source']} — {data['link']}\n")
md.append(f"\n**Caption:**\n\n{data['caption']}\n")
md.append(f"\n**Hashtagler:** {' '.join(data['hashtags'])}\n")
(outdir / "captions.md").write_text("\n".join(md), encoding="utf-8")

print(f"✓ Carousel üretildi: {data['cover_title']}")
print(f"  Slayt sayısı: 1 kapak + {len(data['slides'])} detay + 1 CTA "
      f"= {len(data['slides']) + 2}")
print(f"  Caption: output/{today}/captions.md")
```

- [ ] **Step 2: Çalıştır (curated.json hazır olmalı — Task 2/3 sonrası)**

Run: `python generate.py`
Beklenen: "✓ Carousel üretildi: ..." + "Slayt sayısı: 1 kapak + 3 detay + 1 CTA = 5".

- [ ] **Step 3: posts.json şemasını doğrula**

Run: `python -c "import json; d=json.load(open('data/posts.json',encoding='utf-8')); print(list(d.keys())); print(len(d['slides']), [s['heading'] for s in d['slides']])"`
Beklenen: anahtarlar arasında `cover_title, cover_subtitle, slides, cta_title, cta_subtitle, caption, hashtags, source, link`; `3 ['Ne oldu?', 'Neden önemli?', 'Kuruculara ne anlama geliyor?']`.

- [ ] **Step 4: Kontrol Noktası**

`output/<tarih>/captions.md` dosyasını aç; kapak/slaytlar/CTA/caption/hashtag bölümlerinin dolu ve Türkçe olduğunu gözle doğrula.

---

### Task 5: `make_image.py` — N slaytlık carousel render

Tek kart yerine kapak (Wiro) + detay slaytları (şablon) + CTA slaytını ayrı PNG'ler olarak üret.

**Files:**
- Modify: `make_image.py` (render döngüsü ve çıktı adlandırma yeniden yazılır)

**Interfaces:**
- Consumes: `data/posts.json` (Task 4), `sources.yaml`, `brand/sb-icon-white@2x.png`.
- Produces: `output/<tarih>/slide_1.png … slide_<toplam>.png`.

- [ ] **Step 1: Slayt listesi + render fonksiyonlarını kur**

`make_image.py` içinde, mevcut font/logo/`wrap`/`wiro_background` yardımcıları KORUNUR. `posts = json.loads(...)` satırından sonrasını (eski `for i, p in enumerate(posts, 1):` döngüsü ve sonu) aşağıdaki ile DEĞİŞTİR:

```python
post = json.loads((ROOT / "data" / "posts.json").read_text(encoding="utf-8"))

f_body = load_font(40)   # detay gövde metni

def build_slides(post):
    """posts.json'u render edilecek slayt spec listesine çevirir."""
    slides = [{
        "kind": "cover",
        "title": post["cover_title"],
        "subtitle": post.get("cover_subtitle", ""),
    }]
    for s in post.get("slides", []):
        slides.append({"kind": "detail", "heading": s["heading"], "body": s.get("body", "")})
    slides.append({
        "kind": "cta",
        "title": post["cta_title"],
        "subtitle": post.get("cta_subtitle", "Takip et: @saasbridge"),
    })
    return slides


def draw_chrome(img, d, idx, total, source):
    """Tüm slaytlarda ortak: üst accent, logo+marka, ilerleme, alt bilgi."""
    margin = 90
    d.rectangle([0, 0, W, 12], fill=ACCENT)
    bx = margin
    if LOGO is not None:
        img.paste(LOGO, (margin, 56), LOGO)
        bx = margin + LOGO.width + 24
    d.text((bx, 62), "SAAS BRIDGE", font=f_brand, fill=WHITE)
    d.text((bx, 104), "Haftalık Ekosistem Bülteni", font=f_foot, fill=MUTED)
    # ilerleme göstergesi (sağ üst)
    prog = f"{idx}/{total}"
    pw = d.textlength(prog, font=f_foot)
    d.text((W - margin - pw, 70), prog, font=f_foot, fill=ACCENT)
    # alt bilgi
    d.line([margin, H - 130, W - margin, H - 130], fill=(60, 70, 90), width=2)
    d.text((margin, H - 100), f"Kaynak: {source}", font=f_foot, fill=MUTED)
    d.text((margin, H - 64), "@saasbridge", font=f_foot, fill=ACCENT)
    return margin
```

- [ ] **Step 2: Render döngüsünü ekle (Step 1 bloğunun devamı)**

```python
slides = build_slides(post)
total = len(slides)
today = date.today().isoformat()  # (üstte tanımlı; tekrar zararsız)

for idx, sl in enumerate(slides, 1):
    if sl["kind"] == "cover":
        bg = wiro_background(
            {"visual_title": sl["title"]}, idx
        ) if USE_WIRO else None
    else:
        bg = None

    if bg is None:
        img = Image.new("RGB", (W, H), BG)
    else:
        img = bg
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rectangle([0, 0, W, H], fill=(10, 12, 20, 130))
        od.rectangle([0, 260, W, H], fill=(10, 12, 20, 90))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    d = ImageDraw.Draw(img)
    margin = draw_chrome(img, d, idx, total, post["source"])

    if sl["kind"] in ("cover", "cta"):
        d.rectangle([margin, 300, margin + 70, 312], fill=ACCENT)
        y = 340
        for line in wrap(d, sl["title"], f_title, W - 2 * margin):
            d.text((margin, y), line, font=f_title, fill=WHITE)
            y += 86
        y += 24
        if sl.get("subtitle"):
            for line in wrap(d, sl["subtitle"], f_sub, W - 2 * margin):
                d.text((margin, y), line, font=f_sub, fill=MUTED)
                y += 50
    else:  # detail
        d.rectangle([margin, 300, margin + 70, 312], fill=ACCENT)
        y = 330
        for line in wrap(d, sl["heading"], f_title, W - 2 * margin):
            d.text((margin, y), line, font=f_title, fill=WHITE)
            y += 84
        y += 28
        for line in wrap(d, sl["body"], f_body, W - 2 * margin):
            d.text((margin, y), line, font=f_body, fill=WHITE)
            y += 56

    path = outdir / f"slide_{idx}.png"
    img.save(path)
    bgfile = outdir / f"_bg_{idx}.png"
    if bgfile.exists():
        bgfile.unlink()
    tag = "(Wiro kapak)" if (sl["kind"] == "cover" and bg is not None) else "(şablon)"
    print(f"  ✓ {path.name}  {tag}")

print(f"\nCarousel hazır: output/{today}/  ({total} slayt)")
```
Not: `outdir` make_image.py'de zaten üstte tanımlı; `today` da öyle. Eski `for i, p in enumerate(posts, 1):` bloğu ve eski son `print` TAMAMEN kaldırılmış olmalı.

- [ ] **Step 3: Çalıştır ve PNG'leri üret**

Run: `python make_image.py`
Beklenen: `✓ slide_1.png (Wiro kapak)` (Wiro key varsa) + `slide_2..5.png (şablon)`; `Carousel hazır: output/<tarih>/ (5 slayt)`.

- [ ] **Step 4: Çıktı dosyalarını doğrula**

Run: `python -c "from pathlib import Path; from datetime import date; d=Path('output')/date.today().isoformat(); print(sorted(p.name for p in d.glob('slide_*.png')))"`
Beklenen: `['slide_1.png', 'slide_2.png', 'slide_3.png', 'slide_4.png', 'slide_5.png']`.

- [ ] **Step 5: Görselleri gözle incele**

`output/<tarih>/slide_1.png` … `slide_5.png` dosyalarını aç. Doğrula: kapakta başlık + (varsa) Wiro arka plan; detay slaytlarında başlık + gövde okunabilir; CTA'da soru + "Takip et: @saasbridge"; her slaytın sağ üstünde `k/5`; marka indigo paleti (teal/yeşil yok).

- [ ] **Step 6: Kontrol Noktası**

5 PNG'nin de üretildiğini ve okunabilir olduğunu gözle onayla.

---

### Task 6: `run.py` orkestrasyonu + `sources.yaml` + otomasyon temizliği

Pipeline'a select adımını ekle, ayarları güncelle, zamanlanmış görevi kaldır.

**Files:**
- Modify: `run.py`
- Modify: `sources.yaml`
- Modify: `calistir.bat` (bitiş mesajı)
- Delete: `haftalik.bat`, `son_calisma.log` (varsa)

**Interfaces:**
- Consumes: tüm step script'leri (fetch, curate, select, generate, make_image).

- [ ] **Step 1: `sources.yaml > settings` güncelle**

`settings:` bloğunu şu hale getir (mevcut `num_posts: 3` satırını kaldır, iki yeni anahtar ekle):
```yaml
settings:
  days_lookback: 7          # son kaç günü tara
  max_articles_to_claude: 40  # Claude'a gönderilecek max haber (token kontrolü)
  max_candidates: 15        # kullanıcıya sunulacak aday haber sayısı
  carousel_detail_slides: 3 # kapak ve CTA dışı detay slayt sayısı
  language: "tr"            # caption dili
  brand_name: "SaaS Bridge"
```

- [ ] **Step 2: `run.py`'yi güncelle**

`steps` listesini ve bitiş mesajını değiştir:
```python
steps = [
    ("1/5  Haberler toplanıyor (RSS)",        "fetch.py"),
    ("2/5  Claude aday haberleri hazırlıyor",  "curate.py"),
    ("3/5  Haber seçimi (sen seçeceksin)",     "select.py"),
    ("4/5  Claude carousel metni üretiyor",    "generate.py"),
    ("5/5  Slayt görselleri hazırlanıyor",     "make_image.py"),
]
```
Ve son `print`'i değiştir:
```python
print("\n✅ Bitti. Çıktılar output/<tarih>/ klasöründe "
      "(captions.md + slide_1..N.png)")
```

- [ ] **Step 3: `calistir.bat` bitiş mesajını güncelle**

`calistir.bat` içindeki `(captions.md + post_*.png)` satırını şu yap:
```
echo  (captions.md + slide_*.png)
```

- [ ] **Step 4: Zamanlanmış görevi ve otomasyon dosyalarını kaldır**

Windows görevini sil:
```bash
schtasks //Delete //TN "SaaS Bridge Haftalik" //F
```
Beklenen: "SUCCESS" ya da görev yoksa "ERROR: ... cannot find" (ikisi de kabul; görev artık yok).
Sonra dosyaları sil:
```bash
rm -f haftalik.bat son_calisma.log
```

- [ ] **Step 5: README'de eski akış referanslarını güncelle**

`README.md` içinde `num_posts`, `post_*.png` veya "3 haber/post" geçen ifadeleri yeni akışa göre düzelt: "Pipeline haber listesi sunar, sen bir haber seçersin, seçilen haber 5 slaytlık carousel olur. Çıktı: `slide_1..N.png` + `captions.md`. Zamanlanmış görev kaldırıldı; elle `calistir.bat` ile çalıştır." (Grep ile bul: `grep -n "num_posts\|post_\|haftalik\|Pazartesi\|Task Scheduler" README.md`.)

- [ ] **Step 6: Uçtan uca çalıştır**

Run: `python run.py`
Beklenen: 5 adım sırayla; 3. adımda aday listesi + `Hangi haberi post yapalım? (1-15):` sorusu; numara girince generate + make_image çalışır; sonda `✅ Bitti`. `output/<tarih>/` içinde `slide_1..5.png` + `captions.md`.

- [ ] **Step 7: Kontrol Noktası**

`python run.py` tam akışının (seçim dahil) hatasız tamamlandığını ve 5 slayt + captions.md ürettiğini gözle doğrula. `haftalik.bat`'ın silindiğini ve `schtasks //Query //TN "SaaS Bridge Haftalik"` komutunun "cannot find" döndüğünü doğrula.

---

## Self-Review

**1. Spec coverage:**
- İnteraktif seçim → Task 1+2 (parse_choice + I/O). ✓
- Aday listesi anotasyonu → Task 3 (curate). ✓
- Carousel JSON (kapak/3 detay/CTA/caption) → Task 4 (generate). ✓
- N slayt render, Wiro yalnız kapak, ilerleme göstergesi → Task 5 (make_image). ✓
- run.py 5 adım, sources.yaml ayarları, otomasyon kaldırma, README → Task 6. ✓
- Veri sözleşmeleri (candidates.json / curated.json / posts.json) → Task 2/3/4 interface blokları ve doğrulama adımları. ✓
- Hata durumları: select boş/aralık dışı (Task 2 Step 4), candidates boş (Task 2 Step 1), JSON fence temizliği (Task 3/4), Wiro fallback (Task 5, korunan `wiro_background`). ✓

**2. Placeholder scan:** Kod blokları tam; "TODO/TBD/uygun hata" ifadesi yok. ✓

**3. Type consistency:**
- `parse_choice(raw, n) -> int|None` Task 1'de tanımlı, Task 2'de kullanılıyor. ✓
- candidates.json öğe anahtarları (`reason`,`angle` dahil) Task 3 üretir, Task 2 `format_candidate` tüketir — eşleşiyor. ✓
- posts.json anahtarları (`cover_title`, `cover_subtitle`, `slides[].heading/body`, `cta_title`, `cta_subtitle`, `source`) Task 4 üretir, Task 5 `build_slides`/`draw_chrome` tüketir — eşleşiyor. ✓
- `carousel_detail_slides` Task 6'da yaml'a eklenir, Task 4 okur — eşleşiyor. ✓
