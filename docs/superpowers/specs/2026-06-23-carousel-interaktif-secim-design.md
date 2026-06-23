# Kaydırmalı (Carousel) Post + İnteraktif Haber Seçimi — Tasarım

Tarih: 2026-06-23
Proje: SaaS Bridge haftalık Instagram içerik ajanı

## Amaç

İki davranış değişikliği:

1. **İnteraktif seçim:** Claude'un otomatik 3 haber seçip post üretmesi yerine,
   kullanıcıya detaylı bir haber listesi sunulur; kullanıcı terminalde **tek**
   haber seçer.
2. **Kaydırmalı post:** Seçilen haber tek kart değil, **5 slaytlık carousel**
   olarak görselleştirilir.

## Yeni Pipeline (run.py — 5 adım)

| Adım | Dosya | Durum | Görev |
|------|-------|-------|-------|
| 1 | `fetch.py` | Değişmez | RSS'ten haberleri toplar → `data/articles_raw.json` |
| 2 | `curate.py` | Değişir | En alakalı ~12-15 haberi Claude ile sıralar, her birine kısa `reason` (neden ilgi çekici) + `angle` (önerilen açı) ekler → `data/candidates.json` |
| 3 | `select.py` | YENİ | Adayları terminalde numaralı + detaylı listeler, `Hangi haberi post yapalım? (1-N):` diye sorar; geçerli numara girilince o tek haberi `data/curated.json`'a yazar |
| 4 | `generate.py` | Değişir | Seçilen tek haber için carousel JSON üretir + IG caption/hashtag → `data/posts.json` + `output/<tarih>/captions.md` |
| 5 | `make_image.py` | Değişir | 5 PNG üretir → `output/<tarih>/slide_1.png … slide_5.png` |

## Veri Sözleşmeleri

### data/candidates.json (curate.py çıktısı)
Adayların listesi (sıralı). Her öğe `articles_raw` alanları + `reason` + `angle`:
```json
[
  {"title": "...", "source": "...", "summary": "...", "link": "...",
   "reason": "<1 cümle TR neden>", "angle": "<1 cümle TR açı>"}
]
```

### data/curated.json (select.py çıktısı)
Seçilen **tek** haber (candidates öğesinin aynısı, tek nesne ya da tek elemanlı liste).
Mevcut kodla uyum için tek elemanlı liste tutulur.

### data/posts.json (generate.py çıktısı)
Tek post; carousel yapısı:
```json
{
  "cover_title": "<çarpıcı kısa başlık, max 8 kelime TR>",
  "cover_subtitle": "<1 kısa cümle TR>",
  "slides": [
    {"heading": "Ne oldu?",                 "body": "<2-3 kısa cümle TR>"},
    {"heading": "Neden önemli?",            "body": "<2-3 kısa cümle TR>"},
    {"heading": "Kuruculara ne anlama geliyor?", "body": "<2-3 kısa cümle TR>"}
  ],
  "cta_title": "<kapanış sorusu, TR>",
  "cta_subtitle": "Takip et: @saasbridge",
  "caption": "<Instagram açıklaması, 2-3 paragraf + soru>",
  "hashtags": ["#saas", "..."],
  "source": "...",
  "link": "..."
}
```
Not: detay slayt sayısı `sources.yaml > settings.carousel_detail_slides`
(varsayılan 3) ile kontrol edilir; toplam slayt = 1 kapak + N detay + 1 CTA.

## Görsel Üretimi (make_image.py)

- **Slayt 1 (kapak):** Wiro atmosferik arka plan (tek Wiro çağrısı) + `cover_title` /
  `cover_subtitle`. Wiro yoksa/başarısızsa düz indigo şablona düşer.
- **Slayt 2..N (detay):** Düz indigo marka şablonu; `heading` (vurgu rengi) +
  `body` (sarılmış, okunabilir punto). Metin-yoğun olduğu için gövde için ayrı
  satır-yüksekliği ve alt punto.
- **Son slayt (CTA):** Düz şablon; `cta_title` büyük + `cta_subtitle`.
- Tüm slaytlarda: üst accent çizgi, sol-üstte marka logosu + "SAAS BRIDGE",
  sağ-altta `k/Toplam` ilerleme göstergesi (örn. `2/5`), alt bilgi kaynak/@handle.
- Çıktı adları: `slide_1.png … slide_N.png` (eski `post_N.png` kaldırılır).
- Marka paleti korunur: #2928B6 / #4341D1 / #8B8AE8, koyu indigo zemin.

## Otomasyon

- Windows Task Scheduler görevi **"SaaS Bridge Haftalik" kaldırılır** (input()
  beklediği için takılır). `haftalik.bat` ve `son_calisma.log` referansları
  temizlenir/dosya silinir.
- Tek giriş noktası: `calistir.bat` (elle, çift tık). `run.py` tüm adımları
  sırayla çağırır; 3. adımda kullanıcıdan girdi bekler (subprocess stdin'i
  devralır).

## sources.yaml Değişiklikleri

- `settings.num_posts` artık seçim için kullanılmaz (kaldırılır ya da yok sayılır).
- `settings.max_candidates` (varsayılan 15) — listede gösterilecek aday sayısı.
- `settings.carousel_detail_slides` (varsayılan 3) — kapak ve CTA dışı detay slaytı.

## Hata / Sınır Durumları

- `select.py`: geçersiz/boş girdi → tekrar sorar; aralık dışı numara → uyarı + tekrar.
- Aday listesi boşsa: anlamlı hata mesajı, çıkış kodu ≠ 0 (run.py durdurur).
- Claude JSON parse hatası: mevcut ```json fence temizliği korunur; başarısızlıkta
  ham metni yazdırıp hata ver.
- Wiro başarısız: kapak düz şablona düşer (mevcut davranış korunur).

## Kapsam Dışı (YAGNI)

- Web/menü arayüzü yok (terminal yeterli).
- Slayt başına ayrı Wiro görseli yok (yalnız kapak).
- Çoklu haber/çoklu carousel yok (tek seçim, tek post).
