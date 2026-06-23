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
try:
    data = json.loads(text)
except json.JSONDecodeError as ex:
    print("✗ Claude geçerli JSON döndürmedi. Ham yanıt:\n")
    print(text)
    raise SystemExit(f"JSON ayrıştırma hatası: {ex}")

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
