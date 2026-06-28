# Tasarım: Editöryel Tema + Konu Keşfi + Çalışma-anı Tema Seçimi

Tarih: 2026-06-28
Durum: Onay bekliyor

## Amaç

SaaS Bridge haftalık Instagram pipeline'ına üç yetenek eklemek:

1. **Çalışma anında tema seçimi** — `python run.py` başında kullanıcı tasarımı seçer:
   `CTA Mavi` (mevcut) veya `Editöryel` (Menlo Ventures handoff'undan uyarlanan
   WIRED stili).
2. **Konuya dayalı haber keşfi** — Editöryel tema seçildiğinde kullanıcı serbest
   bir konu/anahtar kelime girebilir (ör. "Dünya Kupası'nda kullanılan SaaS ve AI
   teknolojileri"); ajan Claude'un `web_search` aracıyla canlı web'den ilgili
   güncel haberleri bulur. Boş bırakılırsa mevcut RSS taraması çalışır.
3. **Editöryel tema renderer** — 6 kartlık 1080×1350 carousel'i piksel-mükemmel
   üretmek için HTML şablonu → başsız Chromium (Playwright) → PNG. İçerik
   `posts.json`'dan; fotoğraflar Wiro ile **habere göre** üretilir, görsel dil
   sabit kalır.

Handoff kaynağı: `templates/menlo-ventures-carousel/MenloVenturesCarousel.dc.html`
(Claude Design'dan dışa aktarılan prototip).

## Kapsam dışı (YAGNI)

- CTA Mavi temasının görsel değişikliği — aynen korunur.
- CTA Mavi temasında web arama/konu keşfi — yalnızca editöryelde.
- Otomatik (zamanlanmış) çalışma — pipeline elle çalıştırılmaya devam eder.
- `<image-slot>` etkileşimli web bileşeni — render hattında düz `<img>` kullanılır.

## Onaylanan kararlar (brainstorm)

| Konu | Karar |
|---|---|
| Render yöntemi | Başsız tarayıcı (Playwright/Chromium) → PNG |
| Tema kapsamı | Yeni tema, posts.json-driven; CTA Mavi'nin yanına eklenir |
| Editöryel fotoğraflar | Wiro üretimi, habere uygun, **siyah-beyaz** yüksek kontrast + grain |
| 6. kart | Her zaman sabit "Founders & Investors Night" etkinlik posteri |
| Web arama kapsamı | Sadece editöryel temada |
| Yeni adımlar | `run.py` başında sorulur (tek interaktif giriş noktası) |
| Tema seçimi mekanizması | `make_image.py` dispatcher + `themes/` paketi |

## Mimari

### Genel akış (`run.py`)

```
0. run.py başı (interaktif):
   - Tema sor: 1) CTA Mavi  2) Editöryel
   - Editöryel ise: Konu sor ("boş = haftalık RSS taraması")
   - data/run_config.json yaz: { "theme": "cta_mavi"|"editorial", "topic": "<metin|null>" }

1. Haber toplama:
   - topic varsa → discover.py (Claude + web_search)
   - topic yoksa → fetch.py (RSS, mevcut)

2. curate.py   (değişmez)
3. secim.py    (değişmez)
4. generate.py (değişmez)
5. make_image.py → run_config.theme'e göre render
```

`run_config.json` tek gerçek kaynaktır; adımlar onu okur. Mevcut betikler
(`curate/secim/generate`) hiç değişmez.

### Bileşen 1 — `discover.py` (yeni)

**Sorumluluk:** Bir konuyu canlı web'den güncel haber adaylarına çevirip
`data/articles_raw.json`'a yazmak (fetch.py ile aynı şema).

- Claude Opus 4.8 (`claude-opus-4-8`), adaptive thinking.
- Sunucu-taraflı `web_search_20260209` aracı (`tools=[{"type":
  "web_search_20260209","name":"web_search"}]`). Beta header gerekmez.
- `output_config.format` (json_schema) ile yapılandırılmış çıktı: `articles`
  dizisi; her öğe `{source, title, link, summary, date}`.
- Çıktı şeması fetch.py ile birebir → curate.py değişmeden devam eder.
- Hedef sayı: `sources.yaml > settings.max_candidates` kadar (varsayılan 15).
- Türkçe prompt; marka tonu ve hedef kitle curate.py'deki ile tutarlı.
- Hata/araç sonucu boşsa: anlamlı hata ver, kullanıcıya RSS'e düşmeyi öner.

**Arayüz:** `python discover.py` — `data/run_config.json`'dan `topic` okur,
`data/articles_raw.json` üretir. `_bootstrap` ilk import.

### Bileşen 2 — Tema dispatcher (`make_image.py`) + `themes/` paketi

- `themes/__init__.py`
- `themes/cta_mavi.py` — mevcut `make_image.py` mantığı `render(post, outdir)`
  fonksiyonuna **birebir taşınır** (davranış değişmez; Wiro yok, saf Pillow).
- `themes/editorial.py` — yeni Playwright tabanlı `render(post, outdir)`.
- `make_image.py` — ince dispatcher: `run_config.json`'dan `theme` okur,
  `posts.json`'u yükler, ilgili `render`'ı çağırır. `run_config` yoksa
  varsayılan `cta_mavi`.

### Bileşen 3 — Editöryel renderer (`themes/editorial.py`)

**Adımlar:**

1. `posts.json` + `run_config.json` yükle.
2. **Wiro fotoğrafları** (4 adet): hero (kapak), move (Ne oldu), founder, investor
   (Kuruculara). Her biri için prompt habere göre türetilir (cover_title +
   ilgili slayt başlığından). Wiro modeli `sources.yaml > wiro_model`.
   - Prompt iskeleti: "high-contrast black and white editorial documentary
     photograph about <konu>, photojournalism, no text, no watermark".
   - İndir: `output/<tarih>/_img_hero.png` vb.
   - Hata toleransı: bir görsel üretilemezse o slot için düz koyu gri
     placeholder; render durmaz.
3. **HTML doldur:** Şablon string'i posts.json içeriğiyle ve indirilen görsel
   yollarıyla doldur. `<image-slot>` yerine `<img style="object-fit:cover;
   filter:grayscale(1) contrast(1.05)">`.
4. **Playwright render:** Chromium başlat, HTML'i yükle (file:// veya
   set_content + base_url), `document.fonts.ready` bekle, her `.card`
   section'ı `element.screenshot()` ile `slide_1..6.png`'ye al (1080×1350).
5. Kapanış logu.

**6 kart içerik eşlemesi:**

| Kart | Kaynak (posts.json) | Görsel | Not |
|---|---|---|---|
| 01 Kapak | `cover_title`, `cover_subtitle` | Wiro hero | başlığın son cümleciği maviye boyanır; alt cap `source`'tan |
| 02 Ne oldu? | `slides[0].heading` + `body` | Wiro move | tasarımdaki "$750M→$3B" rozeti **çıkarılır** (jenerik veri yok) |
| 03 Neden önemli? | `slides[1].body` (italik pull-quote) | — | tasarımdaki ek paragraf çıkarılır (tek body var) |
| 04 Kuruculara…? | `slides[2].heading` + `body` | Wiro founder + investor | alt yazılar jenerik/gizli (Menlo'ya özel "Kurucu/Yatırımcı" sabiti değil) |
| 05 CTA | `cta_title` | — | sabit "YORUMLARDA BULUŞALIM →" butonu |
| 06 Poster | — | sabit PNG | `cta-founders-investors-night.png` her zaman |

**Varlıklar (repoya kopyalanır):**
`templates/menlo-ventures-carousel/` altına: `logo-blue.svg`,
`cta-founders-investors-night.png`. (Diğer handoff dosyaları gerekmez.)

**Fontlar:** Tasarımın Google Fonts `<link>`'i korunur (Newsreader + Space Mono);
render öncesi `await page.evaluate("document.fonts.ready")`. Ağ render anında
gerekir (pipeline zaten ağ kullanıyor).

**Grain:** Eksik `grain.png` yerine gömülü SVG `feTurbulence` data-URI; ikili
dosya yok, görsel etki aynı.

**Boyut/keskinlik:** Kartlar tam 1080×1350; `element.screenshot()` o kutuyu
alır. Gerekirse `device_scale_factor=2` + sonradan 1080×1350'e indir (keskinlik).

## Bağımlılıklar

- `playwright` (yeni) — `pip install playwright && playwright install chromium`.
  README'ye kurulum notu; `themes/editorial.py` import edilemezse anlamlı hata.
- Mevcut: `anthropic`, `requests`, `pyyaml`, `feedparser`, `Pillow`.

## Veri sözleşmeleri

`data/run_config.json` (yeni):
```json
{ "theme": "editorial", "topic": "Dünya Kupası'nda SaaS ve AI" }
```

`data/articles_raw.json` (mevcut şema — discover.py de buna uyar):
```json
[ { "source": "...", "title": "...", "link": "...", "summary": "...", "date": "ISO|null" } ]
```

`data/posts.json` (mevcut — değişmez; generate.py üretir).

## Test/doğrulama

- `themes/cta_mavi.py` taşıması sonrası: `theme=cta_mavi` ile `make_image.py`
  eskiyle aynı 5 PNG'yi üretmeli (görsel regresyon yok).
- `discover.py`: örnek bir konuyla çalıştır → `articles_raw.json` şemaya uygun,
  ≥1 öğe. (Gerçek web_search çağrısı; ağ + API anahtarı gerekir.)
- `themes/editorial.py`: örnek `posts.json` ile 6 PNG üret; her biri 1080×1350,
  dosya boyutu > 0; kapakta logo + başlık görünür (gözle bir kez kontrol).
- run.py uçtan uca: editöryel + konu yolu ve cta_mavi + RSS yolu ayrı ayrı.

## Riskler / açık noktalar

- **Playwright kurulumu** ilk sefer Chromium indirir (~150MB). README + ilk
  çalıştırmada net mesaj.
- **web_search maliyeti/kotası** — her keşif çağrısı birden çok arama yapabilir;
  `max_uses` ile sınırlanır.
- **Wiro 4 görsel** — çalıştırma süresi/maliyeti artar (kullanıcı kabul etti).
- **Dinamik başlık → iki-renk boyama** — son cümleciği maviye boyamak basit
  sezgisel; uzun/virgülsüz başlıkta tek renk kalır (kabul edilebilir).
