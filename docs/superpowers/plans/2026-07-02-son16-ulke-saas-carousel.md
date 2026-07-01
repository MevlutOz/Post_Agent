# Son 16 Ülke SaaS Yıldızları Carousel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fransa/Brezilya/Paraguay/Fas'ın en başarılı SaaS ürünlerini tanıtan, son dünya kupası postuyla aynı tasarım dilinde 6 slaytlık IG carousel'i üretmek.

**Architecture:** Mevcut editöryel çok-kart hattı kullanılır: elle yazılmış `data/posts_multi.json` → `make_multi.py` → `themes/editorial_multi.render()` (Wiro S/B fotoğraflar + Playwright PNG). İki kod değişikliği: (1) çalışma ağacındaki commitsiz N-kart genellemesi teste bağlanıp commit'lenir, (2) kapak fotoğrafı verilmediğinde Wiro'dan `_cover.png` üretimi eklenir.

**Tech Stack:** Python 3, pytest, Playwright (Chromium), Wiro görsel API (`wiro_client.py`), PIL.

## Global Constraints

- Tasarım dili 2026-07-01 postuyla birebir aynı; tema dosyalarında görsel stil değişikliği YOK.
- `generate_multi.py` / `discover.py` KULLANILMAZ (Anthropic anahtarı düşük limitli).
- Metinlerde "AI" değil "yapay zeka"; kart gövdeleri Türkçe, 3–4 cümle.
- Gerçek kişi/logo/marka fotoğrafı yok; `image_subject`'ler jenerik S/B sahneler.
- Sayaç kuralı: toplam = kart sayısı + 1 → 4 kartla `00 / 05 … 05 / 05`.
- Testler `python -m pytest tests/ -q` ile depo kökünden koşulur.
- Commit mesajları depodaki Türkçe convention'ı izler (`feat:`, `fix:`, `docs:`).

---

### Task 1: N-kart genellemesini teste bağla ve commit'le

Çalışma ağacında `themes/editorial_html_multi.py` + `themes/editorial_multi.py` içinde
commitsiz duran genelleme (kart sayısı artık 5'e sabit değil; sayaç `len(cards)+1`)
bu işin ön koşulu. Eski davranışı sınayan `test_build_html_multi_trims_to_five`
bilerek düşüyor (7 kart == 6 bekliyor, artık kırpma yok). O test yeni davranış
testiyle değiştirilir, 4-kart senaryosu eklenir, hepsi birlikte commit'lenir.

**Files:**
- Modify: `tests/test_editorial_html_multi.py:61-66` (testi değiştir) ve dosya sonuna 2 test ekle
- Commit'e dahil: `themes/editorial_html_multi.py`, `themes/editorial_multi.py` (mevcut commitsiz değişiklikler — DOKUNMA, sadece commit'le)

**Interfaces:**
- Consumes: `build_html_multi(cards, images, cover=None, cover_image=None)` — kart sayısı serbest, sayaç toplamı `len(cards)+1`.
- Produces: Task 3-4'ün güvendiği davranış: 4 kartla 5 section (cover'sız), cover'la 6 section, sayaçlar `/ 05`.

- [ ] **Step 1: Eski trim testini yeni ölçekleme testiyle değiştir, 4-kart testleri ekle**

`tests/test_editorial_html_multi.py` içinde `test_build_html_multi_trims_to_five`
fonksiyonunu (61-66. satırlar) SİL ve yerine şunu koy:

```python
def test_build_html_multi_scales_beyond_five():
    images = {i: f"_news_{i}.png" for i in range(6)}
    six_cards = CARDS + [{"kick": "z", "title": "altıncı", "body": "x", "source": "y"}]
    html = build_html_multi(six_cards, images)
    assert html.count('class="card"') == 7  # 6 haber + 1 CTA
    assert "altıncı" in html
    assert "06 / 07" in html
    assert 'data-screen-label="07"' in html  # CTA son numarayı alır
```

Dosyanın sonuna da şu iki testi ekle:

```python
def test_build_html_multi_four_cards_counter_is_five():
    images = {i: f"_news_{i}.png" for i in range(4)}
    html = build_html_multi(CARDS[:4], images)
    assert html.count('class="card"') == 5  # 4 haber + 1 CTA
    assert "01 / 05" in html and "04 / 05" in html
    assert 'data-screen-label="05"' in html  # CTA son numarayı alır


def test_cover_card_counter_follows_total():
    html = build_cover_card(COVER, "x.jpg", total=5)
    assert "00 / 05" in html
```

- [ ] **Step 2: Testleri koş — hepsi geçmeli**

Run: `python -m pytest tests/test_editorial_html_multi.py -q`
Expected: `11 passed` (dosyada 9 test vardı: 1'i değiştirildi, 2 yenisi eklendi). Tüm paket: `python -m pytest tests/ -q` → `37 passed`.

- [ ] **Step 3: Genelleme + testleri birlikte commit'le**

```bash
git add themes/editorial_html_multi.py themes/editorial_multi.py tests/test_editorial_html_multi.py
git commit -m "feat: editöryel çok-kart tema N karta genelleme + sayaç testleri"
```

---

### Task 2: Kapak fotoğrafı verilmediğinde Wiro'dan üret

`render()` bugün kapağı yalnızca `cover_image_src` verilmişse basıyor;
`make_multi.py` foto yoksa kapağı iptal ediyor. Yeni davranış: foto verilmemişse
`_cover.png` Wiro'dan üretilir (haber fotoğraflarıyla aynı S/B hat, varsa yeniden
kullanım, hata halinde placeholder).

**Files:**
- Create: `tests/test_editorial_multi.py`
- Modify: `themes/editorial_multi.py` (`_generate_cover_photo` ekle, `render()` kapak bloğu)
- Modify: `make_multi.py:21-27` (kapağı artık iptal etme)

**Interfaces:**
- Consumes: `wiro_client.generate_image(prompt, model=..., width=..., height=...) -> url`, `wiro_client.download(url, dest)`, `build_image_prompt(subject) -> str`, `_placeholder(path)`.
- Produces: `_generate_cover_photo(cover: dict, outdir: Path, model: str) -> str` — üretilen/yeniden kullanılan dosyanın ADI (`"_cover.png"`). `render(cards, outdir, cover=..., cover_image_src=None)` artık kapağı Wiro fotoğrafıyla basar.

- [ ] **Step 1: Failing testleri yaz**

`tests/test_editorial_multi.py` (yeni dosya):

```python
# tests/test_editorial_multi.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import wiro_client
from themes.editorial_multi import _generate_cover_photo

COVER = {"title": "Başlık", "image_subject": "world cup trophy in a stadium"}


def test_cover_photo_generated_via_wiro(tmp_path, monkeypatch):
    calls = {}

    def fake_generate(prompt, model=None, width=None, height=None):
        calls["prompt"] = prompt
        return "http://example/img.png"

    def fake_download(url, dest):
        Path(dest).write_bytes(b"png")

    monkeypatch.setattr(wiro_client, "generate_image", fake_generate)
    monkeypatch.setattr(wiro_client, "download", fake_download)
    name = _generate_cover_photo(COVER, tmp_path, "test-model")
    assert name == "_cover.png"
    assert (tmp_path / "_cover.png").exists()
    assert "world cup trophy" in calls["prompt"]


def test_cover_photo_reused_if_exists(tmp_path, monkeypatch):
    (tmp_path / "_cover.png").write_bytes(b"eski")

    def boom(*a, **k):
        raise AssertionError("Wiro çağrılmamalıydı")

    monkeypatch.setattr(wiro_client, "generate_image", boom)
    name = _generate_cover_photo(COVER, tmp_path, "test-model")
    assert name == "_cover.png"
    assert (tmp_path / "_cover.png").read_bytes() == b"eski"


def test_cover_photo_failure_writes_placeholder(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("api down")

    monkeypatch.setattr(wiro_client, "generate_image", boom)
    name = _generate_cover_photo(COVER, tmp_path, "test-model")
    assert name == "_cover.png"
    assert (tmp_path / "_cover.png").stat().st_size > 0  # placeholder yazıldı
```

- [ ] **Step 2: Testlerin düştüğünü doğrula**

Run: `python -m pytest tests/test_editorial_multi.py -q`
Expected: FAIL — `ImportError: cannot import name '_generate_cover_photo'`.

- [ ] **Step 3: `_generate_cover_photo` + `render()` değişikliği**

`themes/editorial_multi.py` içinde `_generate_photos`'un hemen ALTINA ekle:

```python
def _generate_cover_photo(cover, outdir, model):
    """Kapak için Wiro S/B foto üretir -> dosya adı ('_cover.png').
    Varsa yeniden kullanır; hata halinde placeholder yazar."""
    dest = Path(outdir) / "_cover.png"
    if dest.exists():
        print("    · kapak fotoğrafı mevcut, yeniden kullanılıyor.")
        return dest.name
    subject = cover.get("image_subject") or cover.get("title") or "football stadium"
    try:
        url = wiro_client.generate_image(
            build_image_prompt(subject), model=model, width=1024, height=1024,
        )
        wiro_client.download(url, dest)
    except Exception as ex:
        print(f"    ! Wiro kapak başarısız ({ex}); placeholder.")
        _placeholder(dest)
    return dest.name
```

`render()` içindeki kapak bloğunu (67-71. satırlar: `cover_name = None` … `shutil.copyfile(...)`) şununla değiştir (model çözümü öne alınır, `_generate_photos` çağrısı aynı `model` değişkenini kullanır):

```python
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
```

(Not: `images = _generate_photos(cards, outdir, os.environ.get(...))` satırındaki
eski model ifadesi kaldırılır; `"cover-messi"` sabit adı `"cover"+suffix` olur ve
aynı-dosya kopyalama hatasına karşı guard eklenir.)

- [ ] **Step 4: `make_multi.py` kapağı iptal etmesin**

`make_multi.py` 21-27. satırlardaki blok şu hale gelir:

```python
    # Opsiyonel kapak: posts_multi.json'daki "cover" bloğu. Foto CLI arg ya da
    # COVER_IMAGE env ile verilebilir; verilmezse Wiro'dan _cover.png üretilir.
    cover = data.get("cover")
    cover_img = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("COVER_IMAGE")
    if cover and not cover_img:
        print("  · kapak fotoğrafı verilmedi; Wiro'dan üretilecek (_cover.png).")
```

`render(...)` çağrısı da sadeleşir:

```python
    n = editorial_multi.render(cards, outdir, cover=cover, cover_image_src=cover_img)
```

- [ ] **Step 5: Testler geçsin**

Run: `python -m pytest tests/test_editorial_multi.py -q` → `3 passed`
Run: `python -m pytest tests/ -q` → `40 passed`

- [ ] **Step 6: Commit**

```bash
git add themes/editorial_multi.py make_multi.py tests/test_editorial_multi.py
git commit -m "feat: kapak fotoğrafı verilmezse Wiro'dan _cover.png üretimi"
```

---

### Task 3: posts_multi.json — 4 ülke içeriği

**Files:**
- Modify: `data/posts_multi.json` (tamamen yeni içerikle üzerine yazılır)

**Interfaces:**
- Consumes: `make_multi.py`'nin beklediği şema: `{"cover": {...}, "cards": [...]}`; kick görünümü `"{num} — {KICK}"` (kick'e numara YAZMA).
- Produces: Task 4'ün render edeceği son içerik.

- [ ] **Step 1: Dosyayı şu içerikle yaz**

```json
{
  "cover": {
    "kick": "SON 16 · DÜNYA KUPASI 2026",
    "title": "Dünya Kupasında Son 16'ya Kalan",
    "title_accent": "4 Ülkenin SaaS Yıldızları",
    "subtitle": "Fransa, Brezilya, Paraguay ve Fas sahada tur atlarken, biz de her ülkenin en başarılı SaaS ürününü tek tek açıyoruz.",
    "footer": "KAPAK DOSYASI · 4 ÜLKE",
    "image_subject": "world cup trophy on a pedestal inside a packed football stadium at night, dramatic floodlights, wide shot"
  },
  "cards": [
    {
      "kick": "FRANSA",
      "title": "Doctolib",
      "body": "Fransa'nın sağlık sistemini dijitale taşıyan Doctolib, 90 milyondan fazla kullanıcının randevu ve telesağlık platformu. Yaklaşık 6 milyar euro değerlemesiyle Avrupa'nın en değerli sağlık SaaS'ı. Doktor arayan hasta ile ajandasını yöneten hekim arasındaki köprü artık tek uygulama.",
      "image_subject": "modern doctor's office with a laptop showing a calendar interface, stethoscope on the desk, clean minimal clinic",
      "source": "doctolib.fr"
    },
    {
      "kick": "BREZİLYA",
      "title": "VTEX",
      "body": "Brezilya'dan çıkıp New York borsasına uzanan VTEX, kurumsal e-ticaretin işletim sistemi. Coca-Cola ve Sony gibi devler, 30'dan fazla ülkedeki online mağazalarını bu platformun üzerinde koşturuyor. Latin Amerika'nın en global SaaS başarısı.",
      "image_subject": "large modern e-commerce fulfillment warehouse with conveyor belts and stacked packages, dramatic industrial light",
      "source": "vtex.com"
    },
    {
      "kick": "PARAGUAY",
      "title": "Fiweex",
      "body": "Paraguay'ın genç ekosisteminden bölgesel bir ürün: Fiweex, kafe ve restoranların misafir WiFi'ını bir pazarlama kanalına çeviriyor. Latin Amerika'da 2.500'den fazla işletmede kurulu, 15 milyonu aşkın kayıtlı bağlantıya ulaştı. Küçük pazardan bölgesel SaaS çıkabileceğinin kanıtı.",
      "image_subject": "cozy cafe interior with people using laptops and phones, warm ambient light, wifi router on the wall",
      "source": "fiweex.com"
    },
    {
      "kick": "FAS",
      "title": "Freterium",
      "body": "Kazablanka doğumlu Freterium, üretici ve perakendecilerin nakliye operasyonunu tek bulut platformunda topluyor. Y Combinator destekli ürünün müşterileri Birleşik Arap Emirlikleri'nden Endonezya'ya uzanıyor. Afrika'nın lojistik SaaS'taki en dikkat çekici çıkışı.",
      "image_subject": "fleet of cargo trucks lined up at a logistics hub at dawn, shipping containers in the background",
      "source": "freterium.com"
    }
  ]
}
```

- [ ] **Step 2: JSON geçerliliğini doğrula**

Run: `python -c "import json,pathlib; d=json.loads(pathlib.Path('data/posts_multi.json').read_text(encoding='utf-8')); print(len(d['cards']), bool(d['cover']))"`
Expected: `4 True`

- [ ] **Step 3: Commit**

```bash
git add data/posts_multi.json
git commit -m "feat: son 16 — 4 ülkenin SaaS yıldızları carousel içeriği"
```

---

### Task 4: Render ve görsel doğrulama

**Files:**
- Output: `output/2026-07-02/slide_1..6.png` (+ `_cover.png`, `_news_0..3.png`, `_editorial_multi.html`)

**Interfaces:**
- Consumes: Task 1-3'ün tamamı; Wiro anahtarları ortamda bağlı (bkz. memory), Playwright Chromium kurulu (önceki render'lar bununla yapıldı).

- [ ] **Step 1: Render**

Run: `python make_multi.py`
Expected çıktı sonu: `✓ 6 slayt render edildi → output/2026-07-02/slide_1..6.png`
(5 Wiro çağrısı yapılır: 1 kapak + 4 haber. Bir foto başarısız olursa placeholder ile devam eder — o durumda `_cover.png`/`_news_i.png` silinip yeniden koşulur.)

- [ ] **Step 2: 6 PNG'yi göz ile doğrula (Read tool)**

Kontrol listesi:
- slide_1: kapak — siyah "Dünya Kupasında Son 16'ya Kalan" + mavi "4 Ülkenin SaaS Yıldızları", sayaç `00 / 05`, S/B stadyum bandı.
- slide_2..5: `01 — FRANSA … 04 — FAS` kick'leri, ürün adları serif başlıkta, sayaçlar `01/05 … 04/05`, alt sol köşede kaynak (doctolib.fr vb.), S/B foto sağda.
- slide_6: sabit CTA görseli.
- Metinlerde taşma/kesilme yok; Türkçe karakterler doğru.

- [ ] **Step 3: Çıktı dosyalarını depo convention'ına göre ele al**

Run: `git check-ignore -v output/2026-07-02/slide_1.png; git status --short`
Önceki output klasörleri nasıl ele alınmışsa (ignore/commit) aynısını yap; commit gerekiyorsa:

```bash
git add output/2026-07-02
git commit -m "feat: son 16 ülke SaaS yıldızları carousel render (6 slayt)"
```

- [ ] **Step 4: Son doğrulama**

Run: `python -m pytest tests/ -q` → `40 passed`; `git status` temiz (yalnızca bilinçli untracked'lar: `brand/`, `make_image_koyu_tema_yedek.py` bu işin dışında, DOKUNMA).
