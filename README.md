# SaaS Bridge — Haftalık Instagram Haber Agent

Son 1 haftanın SaaS / AI / AI agent / girişimcilik / yatırım haberlerini
toplar, Claude sıralı aday listesi hazırlar, sen terminalden bir haber seçersin;
seçilen haber 5 slaytlık carousel olur. Instagram caption'ları + marka görselleri
üretir. Çıktıları `output/<tarih>/` klasörüne yazar; sen inceleyip yayınlarsın.

## Kurulum

```bash
pip install feedparser anthropic pyyaml Pillow requests python-dotenv
```

### API anahtarları (.env)

Anahtarlar `.env` dosyasından otomatik okunur (her çalıştırmada export etmene
gerek yok). Proje kökündeki `.env` dosyasını doldur:

```
ANTHROPIC_API_KEY=sk-ant-...        # ZORUNLU — console.anthropic.com
WIRO_API_KEY=...                    # görsel üretimi (opsiyonel)
WIRO_API_SECRET=...                 # sadece signature yöntemi seçtiysen
# WIRO_MODEL=google/nano-banana-pro # sources.yaml'daki modeli override eder
```

> `.env` gizlidir, `.gitignore`'da. Paylaşma. Wiro anahtarları zaten bağlı;
> tek eksik `ANTHROPIC_API_KEY` — onu ekleyince tüm pipeline çalışır.

### Wiro AI görsel üretimi (opsiyonel)

Wiro AI ile habere uygun atmosferik arka plan görseli üretebilirsin. Üstüne
marka + başlık metni yine PIL ile net basılır (zengin ama okunaklı kart).

```bash
export WIRO_API_KEY="..."        # wiro.ai paneli → proje → API key
export WIRO_API_SECRET="..."     # SADECE signature yöntemi seçtiysen gerekli
# Model sources.yaml > wiro_model'den okunur; override için:
# export WIRO_MODEL="google/nano-banana-pro"
```

- **WIRO_API_KEY tanımlıysa** → Wiro arka planı + metin overlay.
- **Tanımlı değilse** → otomatik olarak düz koyu marka şablonuna düşer (sistem her durumda çalışır).
- Wiro çağrısı bir sebeple başarısız olursa o post için sessizce düz şablona düşer.

Proje oluştururken Wiro'da iki kimlik yöntemi var: *API Key Only* (sadece
`WIRO_API_KEY`) veya *Signature-Based* (`WIRO_API_KEY` + `WIRO_API_SECRET`).
İstemci ikisini de destekler — secret tanımlıysa HMAC-SHA256 imzası otomatik üretilir.

## Çalıştırma

```bash
python run.py
```

Pipeline 5 adım sırayla çalışır: RSS toplama → Claude aday listesi → **sen bir haber seçersin** (terminal prompt) → Claude carousel metni → slayt görselleri.

Çıktı: `output/2026-06-23/captions.md` + `slide_1.png`, `slide_2.png` ... `slide_5.png`

Windows'ta çift tıkla çalıştırmak için: **`calistir.bat`**

## Adım adım çalıştırmak istersen

```bash
python fetch.py        # RSS topla → data/articles_raw.json
python curate.py       # Claude aday listesi → data/candidates.json
python secim.py        # terminalden haber seç → data/curated.json
python generate.py     # Claude carousel metni → data/posts.json + captions.md
python make_image.py   # görselleri üret → slide_*.png
```

## Özelleştirme

- **Kaynaklar:** `sources.yaml` → `rss_feeds` listesine ekle/çıkar.
- **Aday sayısı:** `sources.yaml` → `settings.max_candidates` (kaç haber listeleneceği).
- **Detay slayt sayısı:** `sources.yaml` → `settings.carousel_detail_slides`.
- **Marka rengi/fontu:** `make_image.py` üstündeki `BG`, `ACCENT`,
  `BRAND_DEEP/ROYAL/LIGHT` (palet: #2928B6 #4341D1 #8B8AE8) değerleri.
- **Marka logosu:** `brand/` klasöründeki ikonlar. Görsel kartlarda
  `brand/sb-icon-white@2x.png` (beyaz ikon) sol üste basılır.
- **Marka tonu/dili:** `generate.py` içindeki prompt metni.

## Instagram önemli not

Instagram resmi API'si **başka hesapların** gönderilerini çekmene izin vermez
(sadece kendi Business/Creator hesabını yönetebilirsin). Beğendiğin hesaplardan
ilham almak için ilginç gönderi linklerini `sources.yaml` →
`manual_instagram_links` altına elle ekleyebilirsin.

Ana içerik beslemen RSS + haber sitelerinden gelir; bu en sağlam ve sürdürülebilir yoldur.

## Çalıştırma notu

Zamanlanmış görev (Windows Task Scheduler / cron) kaldırıldı. Pipeline interaktif
seçim içerdiğinden tamamen otomatik çalışamaz — her hafta elle `calistir.bat`
(veya `python run.py`) ile başlat, 3. adımda haber numarasını gir.

## Sonraki adımlar (opsiyonel)
- Carousel (çok sayfalı) görsel üretimi
- AI görsel API'si entegrasyonu (DALL·E vb.)
- Otomatik yayınlama (kendi IG Business hesabına Graph API ile)
- Telegram/Slack'e taslak gönderme
