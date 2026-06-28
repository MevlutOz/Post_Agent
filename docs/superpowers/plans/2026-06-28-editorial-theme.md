# Editöryel Tema + Konu Keşfi + Tema Seçimi — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** SaaS Bridge pipeline'ına çalışma-anı tema seçimi (CTA Mavi / Editöryel), konuya dayalı web-arama haber keşfi ve Playwright tabanlı editöryel carousel renderer eklemek.

**Architecture:** `run.py` başında tema (+ editöryelde konu) sorulur, `data/run_config.json`'a yazılır. Konu varsa `discover.py` (Claude + `web_search`) haberleri bulur, yoksa `fetch.py` (RSS). `make_image.py` bir dispatcher olur; `themes/cta_mavi.py` (mevcut Pillow mantığı taşınır) veya `themes/editorial.py` (HTML şablonu → Wiro fotoğrafları → başsız Chromium → PNG) çağrılır.

**Tech Stack:** Python 3, Pillow, anthropic SDK (`claude-opus-4-8` + `web_search_20260209`), Wiro (`wiro_client.py`), Playwright (Chromium), pytest.

## Global Constraints

- Her adım betiği ilk satırda `import _bootstrap` (.env + UTF-8 stdout).
- Seçim modülü ASLA `select.py` adında olmaz (stdlib `select`'i gölgeler).
- Model ID daima `claude-opus-4-8`; adaptive thinking; `web_search_20260209` (beta header yok).
- Çıktı PNG boyutu editöryelde tam **1080×1350**; CTA Mavi mevcut 1080×1350 korunur.
- `data/articles_raw.json` şeması her iki kaynak için aynı: `{source, title, link, summary, date}`.
- Wiro fotoğrafları **siyah-beyaz** yüksek kontrast editöryel; CSS `filter: grayscale(1) contrast(1.05)`.
- 6. kart her zaman sabit `cta-founders-investors-night.png`.
- Testler `tests/` altında; üst-seviye modülü `sys.path.insert(0, parent)` ile import eder (bkz. `tests/test_secim.py`).
- Türkçe kullanıcı metinleri ve promptlar.

---

### Task 1: `runconfig.py` — tema/konu yapılandırması (saf fonksiyonlar + I/O)

**Files:**
- Create: `runconfig.py`
- Test: `tests/test_runconfig.py`

**Interfaces:**
- Produces:
  - `parse_theme_choice(s: str) -> str | None` → `"cta_mavi"` ("1"), `"editorial"` ("2"), aksi halde `None`.
  - `save_run_config(theme: str, topic: str | None, path: Path) -> None` → JSON `{"theme","topic"}` yazar.
  - `load_run_config(path: Path) -> dict` → dosya yoksa `{"theme": "cta_mavi", "topic": None}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runconfig.py
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runconfig import parse_theme_choice, save_run_config, load_run_config


def test_parse_theme_choice():
    assert parse_theme_choice("1") == "cta_mavi"
    assert parse_theme_choice("2") == "editorial"
    assert parse_theme_choice("  2 ") == "editorial"
    assert parse_theme_choice("3") is None
    assert parse_theme_choice("") is None
    assert parse_theme_choice("abc") is None


def test_save_and_load_round_trip(tmp_path):
    p = tmp_path / "run_config.json"
    save_run_config("editorial", "Dünya Kupası SaaS", p)
    cfg = load_run_config(p)
    assert cfg == {"theme": "editorial", "topic": "Dünya Kupası SaaS"}


def test_save_none_topic(tmp_path):
    p = tmp_path / "run_config.json"
    save_run_config("cta_mavi", None, p)
    assert json.loads(p.read_text(encoding="utf-8"))["topic"] is None


def test_load_missing_file_defaults(tmp_path):
    cfg = load_run_config(tmp_path / "yok.json")
    assert cfg == {"theme": "cta_mavi", "topic": None}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_runconfig.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'runconfig'`

- [ ] **Step 3: Write minimal implementation**

```python
# runconfig.py
"""run_config.json okuma/yazma + tema seçimi ayrıştırma (saf)."""
import json
from pathlib import Path

_THEMES = {"1": "cta_mavi", "2": "editorial"}


def parse_theme_choice(s):
    return _THEMES.get((s or "").strip())


def save_run_config(theme, topic, path):
    Path(path).write_text(
        json.dumps({"theme": theme, "topic": topic}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_run_config(path):
    p = Path(path)
    if not p.exists():
        return {"theme": "cta_mavi", "topic": None}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {"theme": data.get("theme", "cta_mavi"), "topic": data.get("topic")}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_runconfig.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add runconfig.py tests/test_runconfig.py
git commit -m "feat: runconfig — tema seçimi + run_config.json yardımcısı"
```

---

### Task 2: Tema dispatcher — `themes/cta_mavi.py` taşı + `make_image.py` ince dispatcher

Mevcut `make_image.py` (saf Pillow, Wiro yok) `themes/cta_mavi.py` içine `render(post, outdir)` olarak taşınır; `make_image.py` yalnızca config okuyup doğru temayı çağırır.

**Files:**
- Create: `themes/__init__.py` (boş)
- Create: `themes/cta_mavi.py`
- Modify: `make_image.py` (tamamen yeniden yazılır — dispatcher)
- Test: `tests/test_cta_mavi.py`

**Interfaces:**
- Consumes: `runconfig.load_run_config` (Task 1)
- Produces: `themes.cta_mavi.render(post: dict, outdir: Path) -> int` (üretilen slayt sayısını döndürür)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cta_mavi.py
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from themes import cta_mavi

SAMPLE = {
    "cover_title": "Tek atılım, 3 milyar dolar",
    "cover_subtitle": "Menlo Ventures'ın Anthropic atılımı zirveyle sonuçlandı.",
    "slides": [
        {"heading": "Ne oldu?", "body": "Menlo 3 milyar dolarlık fonunu kapattı."},
        {"heading": "Neden önemli?", "body": "Tek doğru karar itibarı kurar."},
        {"heading": "Kuruculara ne anlama geliyor?", "body": "Sermaye en güçlü inanandan akar."},
    ],
    "cta_title": "Sen olsan firmanı tek adıma yatırır mıydın?",
    "cta_subtitle": "Takip et: @saasbridge",
    "source": "TechCrunch",
}


def test_render_writes_five_slides_1080x1350(tmp_path):
    n = cta_mavi.render(SAMPLE, tmp_path)
    assert n == 5
    files = sorted(tmp_path.glob("slide_*.png"))
    assert len(files) == 5
    for f in files:
        with Image.open(f) as im:
            assert im.size == (1080, 1350)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cta_mavi.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'themes'`

- [ ] **Step 3a: Create the package marker**

```python
# themes/__init__.py
```
(boş dosya)

- [ ] **Step 3b: Create `themes/cta_mavi.py`**

Mevcut `make_image.py` içeriğini buraya taşı; aşağıdaki **tek yapısal değişiklikle**:
modül seviyesindeki `today` / `outdir` atamalarını ve `main()`'i kaldır; yerine
`render(post, outdir)` koy. Tüm çizim yardımcıları (`stamp_bg`, `draw_faded`,
`wrap`, `fit`, `center_lines`, `coral_bar`, `coral_pill`, `footer`,
`render_cover`, `render_detail`, `render_cta`, `build_slides`, font/logo yükleme
ve renk/boyut sabitleri) **birebir aynı** kalır.

Dosyanın **başı** (sabitler — değişmez kopya):

```python
# themes/cta_mavi.py
"""CTA Mavi tema — posts.json'dan 1080x1350 carousel render eder (saf Pillow).
Eski make_image.py mantığı; tek fark: render(post, outdir) imzası."""
import _bootstrap  # noqa: F401  (.env + UTF-8)
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

S = 2
FW, FH = 1080, 1350
W, H = FW * S, FH * S
def px(v): return int(round(v * S))
# ... (PAPER, BLUE_TOP, ... KICKER_TEXT, font aday listeleri, _font_path,
#      FS_PATH/FR_PATH/FB_PATH, font(), clean_text(), tr_upper(),
#      salient_words(), load_white_logo(), LOGO — make_image.py'den birebir.
#      ÖNEMLİ: make_image.py'de `outdir` modül seviyesindeydi; load_white_logo
#      içindeki `outdir / "_logo_raw.png"` satırını ROOT/"output"/"_tmp" gibi
#      sabit bir yola çevir VEYA logo cache zaten brand/'de olduğundan bu dalın
#      çalışmadığını varsay; basitlik için tmp'i ROOT'a göre yaz.)
```

Dosyanın **sonu** — `main()` yerine:

```python
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
```

Not: `load_white_logo()` içindeki geçici dosya yolu (`outdir / "_logo_raw.png"`)
artık modül-seviye `outdir` olmadığından `ROOT / "output" / "_logo_raw.png"`
olarak değiştirilmeli (klasör yoksa `mkdir(parents=True, exist_ok=True)`).

- [ ] **Step 3c: Rewrite `make_image.py` as dispatcher**

```python
# make_image.py
"""make_image.py — run_config.json'daki temaya göre carousel render eder.
  theme=cta_mavi  → themes/cta_mavi.py (saf Pillow, mevcut tema)
  theme=editorial → themes/editorial.py (Playwright, WIRED editöryel)
İçerik data/posts.json'dan gelir."""
import _bootstrap  # noqa: F401
import json
from pathlib import Path
from datetime import date

from runconfig import load_run_config

ROOT = Path(__file__).resolve().parent


def main():
    post = json.loads((ROOT / "data" / "posts.json").read_text(encoding="utf-8"))
    cfg = load_run_config(ROOT / "data" / "run_config.json")
    theme = cfg["theme"]
    outdir = ROOT / "output" / date.today().isoformat()

    if theme == "editorial":
        from themes import editorial
        n = editorial.render(post, outdir)
    else:
        from themes import cta_mavi
        n = cta_mavi.render(post, outdir)

    print(f"\nCarousel hazır: {outdir}  ({n} slayt, tema={theme})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cta_mavi.py -v`
Expected: PASS (1 passed). (Fontlar Windows'ta mevcut; ağ gerekmez.)

- [ ] **Step 5: Commit**

```bash
git add themes/__init__.py themes/cta_mavi.py make_image.py tests/test_cta_mavi.py
git commit -m "refactor: make_image.py dispatcher + CTA Mavi'yi themes/cta_mavi.py'ye taşı"
```

---

### Task 3: `discover.py` — konuya dayalı web-arama haber keşfi

**Files:**
- Create: `discover.py`
- Test: `tests/test_discover.py`

**Interfaces:**
- Consumes: `runconfig.load_run_config` (Task 1), `wiro`/`anthropic` ortam anahtarları.
- Produces:
  - `build_search_prompt(topic: str, max_n: int, brand: str) -> str` (saf)
  - `ARTICLE_SCHEMA: dict` (json_schema; `articles` dizisi)
  - `main()` → `data/articles_raw.json` yazar.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_discover.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from discover import build_search_prompt, ARTICLE_SCHEMA


def test_prompt_contains_topic_and_count():
    p = build_search_prompt("Dünya Kupası SaaS ve AI", 15, "SaaS Bridge")
    assert "Dünya Kupası SaaS ve AI" in p
    assert "15" in p
    assert "SaaS Bridge" in p


def test_schema_shape():
    props = ARTICLE_SCHEMA["schema"]["properties"]
    item = props["articles"]["items"]["properties"]
    assert set(item.keys()) == {"source", "title", "link", "summary", "date"}
    assert ARTICLE_SCHEMA["schema"]["additionalProperties"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_discover.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'discover'`

- [ ] **Step 3: Write implementation**

```python
# discover.py
"""discover.py — verilen konuyu Claude + web_search ile güncel haber adaylarına
çevirip data/articles_raw.json'a yazar (fetch.py ile aynı şema)."""
import _bootstrap  # noqa: F401
import json
from pathlib import Path
from anthropic import Anthropic

from runconfig import load_run_config

ROOT = Path(__file__).resolve().parent

ARTICLE_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["articles"],
        "properties": {
            "articles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["source", "title", "link", "summary", "date"],
                    "properties": {
                        "source": {"type": "string"},
                        "title": {"type": "string"},
                        "link": {"type": "string"},
                        "summary": {"type": "string"},
                        "date": {"type": "string"},
                    },
                },
            }
        },
    },
}


def build_search_prompt(topic, max_n, brand):
    return (
        f"Sen {brand} adlı Türkiye SaaS & AI topluluğunun haber editörüsün.\n"
        f"Konu: \"{topic}\".\n"
        f"web_search aracını kullanarak bu konuyla ilgili EN GÜNCEL, güvenilir "
        f"ve ilgi çekici en fazla {max_n} haber bul. Hedef kitle: SaaS/AI "
        f"kurucuları ve yatırımcıları. Magazinsel/alakasız olanları ele.\n"
        f"Her haber için kaynağın adını, başlığı, gerçek URL'yi, 1-2 cümlelik "
        f"özeti ve yayın tarihini (ISO 8601, bilinmiyorsa boş) ver.\n"
        f"SADECE şemaya uygun JSON döndür."
    )


def main():
    cfg = load_run_config(ROOT / "data" / "run_config.json")
    topic = cfg.get("topic")
    if not topic:
        raise SystemExit("discover.py: run_config.json'da topic yok.")

    import yaml
    settings = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))["settings"]
    max_n = settings.get("max_candidates", 15)
    brand = settings["brand_name"]

    client = Anthropic()
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        tools=[{"type": "web_search_20260209", "name": "web_search",
                "max_uses": 8}],
        output_config={"format": ARTICLE_SCHEMA},
        messages=[{"role": "user", "content": build_search_prompt(topic, max_n, brand)}],
    )
    text = next((b.text for b in resp.content if b.type == "text"), "")
    articles = json.loads(text)["articles"][:max_n]

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "articles_raw.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ '{topic}' için {len(articles)} haber bulundu → data/articles_raw.json")
    for i, a in enumerate(articles, 1):
        print(f"  {i}. {a['title'][:70]}")


if __name__ == "__main__":
    main()
```

> Not: `output_config.format` + `web_search` birlikte kullanımı belgelenmiştir;
> eğer API bu kombinasyonu reddederse fallback: `output_config.format`'ı kaldır,
> prompt'a "SADECE şu JSON formatında yanıt ver" ekleyip yanıttan JSON ayrıştır
> (curate.py'deki `replace("```json","")` deseni gibi).

- [ ] **Step 4: Run unit test to verify it passes**

Run: `python -m pytest tests/test_discover.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Manual integration verification**

`data/run_config.json` → `{"theme":"editorial","topic":"yapay zeka ajanları VC yatırımı"}` yaz, sonra:
Run: `python discover.py`
Expected: `data/articles_raw.json` oluşur, ≥1 öğe, her öğede 5 alan dolu, URL'ler gerçek.

- [ ] **Step 6: Commit**

```bash
git add discover.py tests/test_discover.py
git commit -m "feat: discover.py — konuya dayalı web_search haber keşfi"
```

---

### Task 4: Editöryel HTML şablonu (saf yardımcılar)

**Files:**
- Create: `themes/editorial_html.py`
- Test: `tests/test_editorial_html.py`

**Interfaces:**
- Produces:
  - `color_last_clause(title: str) -> str` → başlığın son cümleciğini `<span style="color:#0050EE;">…</span>` ile sarar (HTML-escape'li); virgül/nokta yoksa tüm başlık düz döner.
  - `build_image_prompt(subject: str) -> str` → Wiro için S/B editöryel foto prompt'u.
  - `card_payload(post: dict) -> dict` → `{cover_title, cover_subtitle, slides[3], cta_title, source}` normalize eder (eksik alanları boş stringe çevirir).
  - `build_html(post: dict, images: dict) -> str` → tam 6-kartlık HTML. `images` = `{"hero","move","founder","investor"}` dosya yolları.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_editorial_html.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'themes.editorial_html'`

- [ ] **Step 3: Write implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_editorial_html.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add themes/editorial_html.py tests/test_editorial_html.py
git commit -m "feat: editöryel HTML şablonu (saf, 6 kart) + testler"
```

---

### Task 5: Editöryel renderer — varlıklar + Wiro fotoğrafları + Playwright

**Files:**
- Create: `themes/editorial.py`
- Create (kopya): `templates/menlo-ventures-carousel/logo-blue.svg`, `templates/menlo-ventures-carousel/cta-founders-investors-night.png`, `templates/menlo-ventures-carousel/MenloVenturesCarousel.dc.html` (referans)
- Test: `tests/test_editorial.py` (sadece saf yardımcı `photo_subjects`)

**Interfaces:**
- Consumes: `themes.editorial_html.build_html`, `themes.editorial_html.build_image_prompt`, `wiro_client.generate_image/download`.
- Produces: `themes.editorial.render(post: dict, outdir: Path) -> int` (6 döndürür); `themes.editorial.photo_subjects(post: dict) -> dict` (saf).

- [ ] **Step 1: Copy assets into the repo**

```bash
SRC="$HOME/AppData/Local/Temp/claude"  # scratchpad ui-handoff kökü
mkdir -p "templates/menlo-ventures-carousel"
# Aşağıdaki yolu extracted handoff'a göre düzelt:
# .../scratchpad/ui-handoff/saasbridge-ui/project/templates/menlo-ventures-carousel/
cp ".../logo-blue.svg" templates/menlo-ventures-carousel/
cp ".../../../uploads/cta-founders-investors-night.png" templates/menlo-ventures-carousel/
cp ".../MenloVenturesCarousel.dc.html" templates/menlo-ventures-carousel/
```
Doğrula: `ls templates/menlo-ventures-carousel/` → `logo-blue.svg`,
`cta-founders-investors-night.png`, `MenloVenturesCarousel.dc.html` görünmeli.

- [ ] **Step 2: Write the failing test (saf yardımcı)**

```python
# tests/test_editorial.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from themes.editorial import photo_subjects

POST = {
    "cover_title": "Menlo Ventures 3 milyar dolarlık fonunu kapattı",
    "slides": [
        {"heading": "Ne oldu?", "body": "..."},
        {"heading": "Neden önemli?", "body": "..."},
        {"heading": "Kuruculara ne anlama geliyor?", "body": "..."},
    ],
}


def test_photo_subjects_keys_and_nonempty():
    subj = photo_subjects(POST)
    assert set(subj.keys()) == {"hero", "move", "founder", "investor"}
    assert all(subj.values())
    assert "Menlo" in subj["hero"]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_editorial.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'themes.editorial'`

- [ ] **Step 4: Write implementation**

```python
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
    """Her foto slotu için Wiro konu metni (habere göre)."""
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
            url = wiro_client.generate_image(build_image_prompt(subject),
                                             model=model, width=1024, height=1024)
            wiro_client.download(url, dest)
        except Exception as ex:
            print(f"    ! Wiro '{key}' başarısız ({ex}); placeholder kullanılıyor.")
            _placeholder(dest)
        paths[key] = dest.name  # HTML aynı klasörden çözecek
    return paths


def render(post, outdir):
    """posts.json post'unu editöryel temada 6 PNG olarak render eder."""
    from playwright.sync_api import sync_playwright

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Şablon varlıklarını çıktı klasörüne kopyala (HTML göreli yolla bulur)
    for asset in ("logo-blue.svg", "cta-founders-investors-night.png"):
        shutil.copyfile(TEMPLATE_DIR / asset, outdir / asset)

    images = _generate_photos(post, outdir, os.environ.get("WIRO_MODEL")
                              or _wiro_model())
    html = build_html(post, images)
    html_path = outdir / "_editorial.html"
    html_path.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT},
                                device_scale_factor=2)
        page.goto(html_path.as_uri())
        page.wait_for_function("document.fonts.ready")
        page.wait_for_timeout(400)  # webfont boyama
        cards = page.query_selector_all("section.card")
        for idx, card in enumerate(cards, 1):
            card.screenshot(path=str(outdir / f"slide_{idx}.png"))
        browser.close()

    # device_scale_factor=2 → 2160x2700; 1080x1350'e indir
    for f in sorted(outdir.glob("slide_*.png")):
        with Image.open(f) as im:
            if im.size != (WIDTH, HEIGHT):
                im.resize((WIDTH, HEIGHT), Image.LANCZOS).save(f)
    return len(list(outdir.glob("slide_*.png")))


def _wiro_model():
    import yaml
    cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
    return cfg.get("wiro_model", "google/nano-banana-pro")
```

- [ ] **Step 5: Run unit test to verify it passes**

Run: `python -m pytest tests/test_editorial.py -v`
Expected: PASS (1 passed)

- [ ] **Step 6: Install Playwright + Chromium**

```bash
pip install playwright
python -m playwright install chromium
```

- [ ] **Step 7: Manual integration verification**

Geçerli bir `data/posts.json` ile (önceki çalıştırmadan veya örnekle):
```python
# scratch: python -c
import json, sys; sys.path.insert(0,".")
from pathlib import Path
from themes import editorial
post = json.loads(Path("data/posts.json").read_text(encoding="utf-8"))
print(editorial.render(post, Path("output/_editorial_test")))
```
Expected: `output/_editorial_test/slide_1..6.png`, her biri 1080×1350; kapakta
logo + iki-renk başlık; foto kartlarında S/B çerçeveli görseller; kart 6 poster.
(Wiro+ağ gerekir; Wiro kapalıysa koyu placeholder'lar gelir, render yine 6 PNG.)

- [ ] **Step 8: Commit**

```bash
git add themes/editorial.py tests/test_editorial.py templates/menlo-ventures-carousel/
git commit -m "feat: editöryel renderer — Wiro S/B fotoğraflar + Playwright PNG + varlıklar"
```

---

### Task 6: `run.py` — başta tema + konu sor, 1. adımı yönlendir

**Files:**
- Modify: `run.py` (tamamen yeniden yazılır)

**Interfaces:**
- Consumes: `runconfig.parse_theme_choice`, `runconfig.save_run_config` (Task 1).

- [ ] **Step 1: Rewrite `run.py`**

```python
# run.py
"""run.py — Tüm pipeline'ı tek komutla çalıştırır.
Başta tasarım teması (editöryelde ayrıca konu) sorulur.
Kullanım:  python run.py  (ya da çift tık: calistir.bat)"""
import _bootstrap  # noqa: F401
import subprocess, sys
from pathlib import Path

from runconfig import parse_theme_choice, save_run_config

ROOT = Path(__file__).resolve().parent


def ask_setup():
    print("Hangi tasarım? 1) CTA Mavi (mevcut)   2) Editöryel (Menlo/WIRED)")
    theme = None
    while theme is None:
        theme = parse_theme_choice(input("Seçim (1/2): "))
        if theme is None:
            print("Lütfen 1 ya da 2 gir.")
    topic = None
    if theme == "editorial":
        topic = input("Konu gir (boş = haftalık RSS taraması): ").strip() or None
    save_run_config(theme, topic, ROOT / "data" / "run_config.json")
    return theme, topic


def main():
    (ROOT / "data").mkdir(exist_ok=True)
    theme, topic = ask_setup()

    fetch_step = ("1/5  Konuya göre haberler aranıyor (web)", "discover.py") if topic \
        else ("1/5  Haberler toplanıyor (RSS)", "fetch.py")
    steps = [
        fetch_step,
        ("2/5  Claude aday haberleri hazırlıyor", "curate.py"),
        ("3/5  Haber seçimi (sen seçeceksin)", "secim.py"),
        ("4/5  Claude carousel metni üretiyor", "generate.py"),
        ("5/5  Slayt görselleri hazırlanıyor", "make_image.py"),
    ]
    for label, script in steps:
        print(f"\n{'='*50}\n{label}\n{'='*50}", flush=True)
        if subprocess.run([sys.executable, str(ROOT / script)]).returncode != 0:
            print(f"\n✗ Hata: {script} adımında durdu.")
            sys.exit(1)

    print("\n✅ Bitti. Çıktılar output/<tarih>/ klasöründe "
          "(captions.md + slide_1..N.png)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify run.py imports cleanly**

Run: `python -c "import ast; ast.parse(open('run.py',encoding='utf-8').read()); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Manual end-to-end (CTA Mavi + RSS yolu)**

Run: `python run.py` → "1" seç → akış `fetch.py` ile başlar, sonda
`output/<tarih>/slide_1..5.png` (CTA Mavi). Haber seçim adımında bir numara gir.

- [ ] **Step 4: Manual end-to-end (Editöryel + konu yolu)**

Run: `python run.py` → "2" seç → konu gir (ör. "AI ajanlarına VC yatırımı") →
akış `discover.py` ile başlar; sonda `output/<tarih>/slide_1..6.png` (editöryel).

- [ ] **Step 5: Commit**

```bash
git add run.py
git commit -m "feat: run.py başında tema+konu seçimi; 1. adımı discover/fetch'e yönlendir"
```

---

### Task 7: Bağımlılıklar + README

**Files:**
- Create: `requirements.txt`
- Modify: `README.md`

- [ ] **Step 1: Create `requirements.txt`**

```
anthropic
requests
pyyaml
feedparser
Pillow
python-dotenv
playwright
```

- [ ] **Step 2: Update README — yeni akış + kurulum**

`README.md`'ye ekle (uygun bölüme):
- Kurulum: `pip install -r requirements.txt` ve `python -m playwright install chromium`.
- Yeni akış: `python run.py` başta **tema** sorar (1=CTA Mavi, 2=Editöryel);
  editöryel seçilince **konu** sorar (boş = RSS). Konu verilince haberler web'den
  aranır (`discover.py`), aksi halde RSS (`fetch.py`).
- Editöryel tema: 6 kart, Wiro S/B fotoğraflar, 6. kart sabit etkinlik posteri;
  Playwright/Chromium gerekir.
- Tema kodu `themes/` altında (`cta_mavi.py`, `editorial.py`).

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest -v`
Expected: tüm testler PASS (runconfig, cta_mavi, discover, editorial_html, editorial, secim).

- [ ] **Step 4: Commit**

```bash
git add requirements.txt README.md
git commit -m "docs: requirements.txt + README editöryel tema/konu akışı"
```

---

## Self-Review notları

- **Spec kapsamı:** A (discover.py=Task 3, run.py yönlendirme=Task 6), B (dispatcher=Task 2, run.py soru=Task 6, runconfig=Task 1), C (editorial_html=Task 4, editorial render+Wiro+Playwright+varlıklar=Task 5). 6 kart eşlemesi, S/B foto, sabit poster, grain SVG, font bekleme — hepsi karşılandı.
- **Placeholder taraması:** Tüm kod adımlarında gerçek kod var. Tek "düzeltilecek yol" varlık kopyalama komutundaki scratchpad mutlak yolu (ortam-bağımlı, kaçınılmaz) — uygulayıcı `ls` ile doğrular.
- **Tip tutarlılığı:** `render(post, outdir)` her iki temada aynı imza; `build_html(post, images)` ve `images` anahtarları (`hero/move/founder/investor`) Task 4 ve 5'te birebir; `parse_theme_choice/save_run_config/load_run_config` Task 1↔2↔6 tutarlı.
