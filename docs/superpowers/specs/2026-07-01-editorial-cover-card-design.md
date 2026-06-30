# Editöryel Kapak Kartı (Cover) — Tasarım

2026-07-01. "5 haber + sabit CTA" editöryel carousel'ine (bkz.
`2026-06-30-multi-news-editorial-design.md`) bir **kapak kartı (00)** ekler ve
haber metinlerindeki "AI" ifadesini "yapay zeka" ile değiştirir.

## Amaç
2026 Dünya Kupası dosyasına markaya uygun bir açılış görseli kazandırmak.
Kullanıcının verdiği Messi + kupa fotoğrafı, mevcut tasarım dilinin
`grayscale(1) contrast` filtresi + siyah çerçeve + sert gölge + grain
katmanıyla otomatik olarak S/B editöryel diline dönüştürülür (ayrıca fiziksel
B&W işleme gerekmez).

## Kapak kartı düzeni (onaylı)
1080×1350, beyaz zemin, Newsreader serif + Space Mono, mavi `#0050EE`.
- Header: SaaSbridge mavi logo + `00 / 06` sayaç.
- Siyah tag pill: `DOSYA · DÜNYA KUPASI 2026`.
- Büyük serif manşet: "Şampiyonluğun **Görünmeyen Teknolojisi**" — son kısım
  (`title_accent`) mavi.
- Alt metin: "Bir şampiyonluğun arkasındaki SaaS & yapay zeka altyapısı: 5 ders."
- **Başlığın altında tam genişlik foto bandı** (≈932×420), Messi fotoğrafı;
  `object-position:center ~28%` ile yüz+kupa korunur, alt/üst kırpılır.
- Footer: `KAPAK DOSYASI · 5 DERS` + mavi `Kaydır →`.

## Numaralandırma
Kapak = `00 / 06`, haberler `01–05 / 06`, CTA `06`. Böylece mevcut haber/CTA
sayaçları değişmez; toplam 7 slayt (00–06).

## Kod değişiklikleri
1. `themes/editorial_html_multi.py`
   - Yeni saf fonksiyon `build_cover_card(cover, image_name)`.
   - `build_html_multi(cards, images, cover=None, cover_image=None)` — opsiyonel
     kapak parametresi; cover verilmezse mevcut 6 kartlık çıktı **birebir korunur**
     (geriye dönük uyum, mevcut testler geçer).
   - CSS'e `.tag` kuralı eklenir (multi şablonunda yoktu).
2. `themes/editorial_multi.py`
   - Kapak görselini `cover-messi.jpg` olarak çıktı klasörüne kopyalar.
   - `_generate_photos`: bir `_news_{i}.png` zaten varsa **yeniden kullanır**
     (Wiro çağrısı yok — hız + düşük rate-limit dostu); yoksa üretir.
   - `render(cards, outdir, cover=None, cover_image_src=None)` 7 slayt üretir.
3. `data/posts_multi.json` — "AI" → "yapay zeka" (kicker, gövde, caption).
4. `make_multi.py` — kapak verisini ve kullanıcının fotoğraf yolunu geçirir.
5. Test: `tests/test_editorial_html_multi.py` — `build_cover_card` ve cover'lı
   `build_html_multi` için yeni testler.

## Test stratejisi
Saf HTML fonksiyonları unit-test (pytest, `sys.path.insert` deseni). Wiro/
Playwright render manuel doğrulanır (kapak slaytı görsel onayı).
