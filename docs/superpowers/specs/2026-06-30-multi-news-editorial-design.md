# Spec: 5 Haber + CTA editöryel carousel (2026-06-30)

## Amaç
Editöryel tasarım dilinde, **tek haberi bölmek yerine** 5 ayrı haberi her biri
tek bir kartta sunan bir Instagram carousel'i. Konu: 2026 Dünya Kupası'nda
kullanılan SaaS & yapay zeka teknolojileri. 6. kart sabit "Founders &
Investors Night" CTA görselidir. Her haber kartının görseli kendi haberine özgü.

## Çıktı
- 6 PNG (1080×1350), `output/<tarih>/slide_1..6.png`
- `data/posts_multi.json`, `output/<tarih>/captions.md`

## Tasarım dili (mevcut editöryelden devralınır)
Newsreader serif + Space Mono, mavi #0050EE, mercan #FB6A5F vurgu, S/B yüksek
kontrast grenli foto (CSS grayscale+contrast), siyah 2.5px çerçeve + 16px sert gölge.

## Kart düzeni
- **Kart 1–5 (haber):** "yan yana" — üstte logo + `0X / 06` + ince çizgi; solda
  `0X — ETİKET` (kick), serif bold başlık, 1–2 cümle gövde; sağda o habere özel
  dikey S/B foto (çerçeve + sert gölge); altta kaynak + @saasbridge.
- **Kart 6 (CTA):** sabit `cta-founders-investors-night.png` (değişmez).

## Veri akışı
1. `curate.py` → `data/candidates.json` (hâlihazırda 6 aday hazır; ilk 5 kullanılır).
2. `generate_multi.py` — **tek** Claude çağrısı (`claude-opus-4-8`). Girdi: ilk 5
   aday (title/source/summary/angle). Çıktı JSON şeması:
   ```json
   {
     "cards": [
       {"kick": "<kısa etiket, TR, max 3 kelime>",
        "title": "<serif başlık, max 9 kelime, TR>",
        "body": "<1-2 cümle, TR>",
        "image_subject": "<EN photo subject, no text>"}
     ],
     "caption": "<IG açıklaması: 5 haberi özetle + Founders&Investors Night daveti>",
     "hashtags": ["#saas", "#yapayzeka", ...]
   }
   ```
   `cards` tam 5 öğe. Her karta aday `source`+`link` koddan eklenir.
   → `data/posts_multi.json` + `captions.md`.
3. `themes/editorial_html_multi.py` (saf) — `build_news_card(i, card, image_name)`
   ve `build_html_multi(cards, images)` → 5 haber kartı + sabit CTA kartı HTML'i.
4. `themes/editorial_multi.py` — 5 Wiro fotoğrafı (her kart için `image_subject`,
   `build_image_prompt` ile S/B editöryel), Playwright Chromium → 6 PNG (mevcut
   `editorial.py` render mantığı: çerçeve kopyalama, font bekleme, 2x ölçek indirme).
5. `make_multi.py` — `posts_multi.json` yükler, render eder.

## Hata yönetimi
- Wiro foto başarısızsa gri placeholder (mevcut davranış).
- Claude geçersiz JSON → ham yanıtı yazdır + SystemExit.
- Rate limit (org 10k token/dk, 5 istek/dk): generate_multi TEK çağrı; gerekirse
  retry-after kadar bekle.

## Test
Saf yardımcılar pytest ile (`sys.path.insert` deseni, API'siz):
- `build_news_card` başlık/gövde/kaynak/sayaç/görsel adını içerir, HTML-escape eder.
- `build_html_multi` 6 `<section class="card">` üretir; 6. kart sabit PNG'yi içerir.
- ilk-5 kırpma (5'ten az aday → olanı kullan).

## Kapsam dışı (YAGNI)
CTA görselini değiştirme, kart sayısını parametrik yapma, yeni tema seçenekleri.
