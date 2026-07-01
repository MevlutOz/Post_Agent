# Son 16 Ülke SaaS Yıldızları — Editöryel Carousel (2026-07-02)

## Amaç

Dünya Kupası'nda son 16'ya kalan dört ülkenin (Fransa, Brezilya, Paraguay, Fas)
en popüler/başarılı SaaS ürününü tanıtan tek bir Instagram carousel'i üretmek.
Tasarım dili 2026-07-01 dünya kupası postuyla birebir aynı (editöryel çok-kart tema).

## Kapsam ve format

Tek carousel, 6 slayt:

| Slayt | İçerik |
|---|---|
| 00 | Kapak: siyah üst satır "Dünya Kupasında Son 16'ya Kalan" + mavi accent "4 Ülkenin SaaS Yıldızları", tek cümle alt yazı, tam genişlik S/B foto bandı (Wiro üretimi stadyum/kupa sahnesi) |
| 01 | Kick `01 — FRANSA`, başlık **Doctolib** — Avrupa'nın en değerli sağlık SaaS'ı (~€6 milyar, 90M+ kullanıcı, randevu + telesağlık) |
| 02 | Kick `02 — BREZİLYA`, başlık **VTEX** — NYSE'de işlem gören global e-ticaret platformu (Coca-Cola, Sony gibi müşteriler) |
| 03 | Kick `03 — PARAGUAY`, başlık **Fiweex** — WiFi marketing SaaS'ı, LATAM'da 2.500+ işletme, 15M+ kayıtlı bağlantı |
| 04 | Kick `04 — FAS`, başlık **Freterium** — YC destekli bulut lojistik/nakliye yönetimi (TMS), BAE'den Endonezya'ya müşteri |
| 05 | Sabit CTA: Founders & Investors Night görseli (değişmez) |

Sayaç: `00 / 05 … 05 / 05` (toplam = kart sayısı + 1, kapak 00).

## İçerik kuralları

- Kart gövdeleri Türkçe, 3–4 cümle, son postun editöryel tonunda: ne yapar,
  ne kadar büyük, neden o ülkenin yıldızı. "AI" yerine "yapay zeka".
- Her kartın `image_subject`'i ürünün alanını çağrıştıran S/B sahne
  (muayenehane/dijital randevu, e-ticaret deposu, kafe WiFi, lojistik filo).
  Gerçek kişi/logo/marka görseli yok.
- `source` alanı ürünün resmi sitesi (kart altbilgisinde görünür).

## Teknik akış

1. Çalışma ağacındaki commitsiz N-kart genellemesi (`themes/editorial_html_multi.py`,
   `themes/editorial_multi.py`) bu işin ön koşulu → önce test edilip commit'lenir.
2. `data/posts_multi.json` elle yazılır (cover + 4 kart). `generate_multi.py`/
   `discover.py` KULLANILMAZ (Anthropic düşük limit; içerik zaten kürasyonlu).
3. Kapak fotoğrafı: `make_multi.py`'ye küçük ekleme — `cover` tanımlı ama
   foto verilmemişse Wiro'dan `_cover.png` üretilir (cover'daki `image_subject`
   alanından; kart fotoğraflarıyla aynı S/B hat). Mevcut arg/COVER_IMAGE
   davranışı korunur; verilmişse Wiro çağrılmaz.
4. `make_multi.py` çalıştırılır → `output/2026-07-02/slide_1..6.png`.

## Hata durumları

- Wiro foto üretimi başarısız olursa: mevcut davranış korunur (hata net
  raporlanır, eksik fotoğrafla render edilmez).
- `_cover.png` / `_news_i.png` zaten varsa yeniden kullanılır (mevcut davranış).

## Test

- Mevcut test paketi (31 test) commitsiz genellemeyle geçmeli.
- `make_multi.py` kapak-Wiro eklemesi için: cover'lı/coversız, foto verilmiş/
  verilmemiş durumlarını kapsayan birim test(ler).
- Görsel doğrulama: render edilen 6 PNG göz ile kontrol (sayaç, kick, başlık,
  foto yerleşimi son postla tutarlı).

## Başarı kriteri

`output/2026-07-02/` altında son postla aynı tasarım dilinde, yayına hazır
6 slayt PNG + kart metinlerinin doğruluğu (ürün bilgileri araştırmayla uyumlu).
