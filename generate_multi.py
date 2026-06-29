"""
generate_multi.py — Claude API (TEK çağrı): candidates.json'daki ilk 5 haberi,
her biri tek bir editöryel karta gelecek şekilde içeriğe dönüştürür.
Çıktı: data/posts_multi.json + output/<tarih>/captions.md
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

N = 5
candidates = json.loads((ROOT / "data" / "candidates.json").read_text(encoding="utf-8"))[:N]

listing = "\n".join(
    f"[{i}] ({c.get('source','?')}) {c.get('title','')} — {c.get('summary','')[:240]} "
    f"| Önerilen açı: {c.get('angle','')}"
    for i, c in enumerate(candidates)
)

prompt = f"""Sen {brand} adlı, Türkiye SaaS & AI ekosistemine odaklanan topluluğun
Instagram içerik yazarısın. Marka tonu: bilgili ama samimi, kurucu-dostu, abartısız, Türkçe.
Hedef kitle: SaaS/AI kurucuları ve yatırımcılar.

Aşağıda {len(candidates)} haber var. Her biri kaydırmalı (carousel) bir Instagram
postunda AYRI bir kart olacak (toplam {len(candidates)} haber kartı + 1 sabit CTA kartı).
Her haber için kısa, çarpıcı bir kart metni üret. Sırayı KORU.

Her kart için:
- kick: kısa üst etiket, BÜYÜK harfe uygun, max 3 kelime, TR (örn "AI OFSAYT", "EĞİTİM VERİSİ")
- title: serif başlık, max 9 kelime, çarpıcı, TR
- body: 1-2 kısa cümle, o haberi kurucuya bağlayan öz, TR
- image_subject: o habere uygun, metinsiz bir İNGİLİZCE belgesel-fotoğraf konusu
  (örn "semi-automated offside camera system in a stadium, referee"); kişi/marka logosu yok

SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{{
  "cards": [
    {{"kick": "...", "title": "...", "body": "...", "image_subject": "..."}}
  ],
  "caption": "<IG açıklaması: {len(candidates)} haberi tek paragrafta özetle, kurucu/yatırımcıya 'ne anlama geliyor' bağla; sonunda 'Founders & Investors Night'a davet et. Emoji ölçülü>",
  "hashtags": ["#saas", "#yapayzeka", "#dünyakupası"]
}}
"cards" tam {len(candidates)} öğe içermeli ve haber sırasını korumalı.

Haberler:
{listing}
"""

resp = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=3000,
    messages=[{"role": "user", "content": prompt}],
)
text = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
try:
    data = json.loads(text)
except json.JSONDecodeError as ex:
    print("✗ Claude geçerli JSON döndürmedi. Ham yanıt:\n")
    print(text)
    raise SystemExit(f"JSON ayrıştırma hatası: {ex}")

cards = data.get("cards", [])[:N]
# Her karta kaynak + link'i koddan ekle (sıra korunur)
for i, card in enumerate(cards):
    if i < len(candidates):
        card["source"] = candidates[i].get("source", "")
        card["link"] = candidates[i].get("link", "")

out = {
    "cards": cards,
    "caption": data.get("caption", ""),
    "hashtags": data.get("hashtags", []),
}
(ROOT / "data" / "posts_multi.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)

today = date.today().isoformat()
outdir = ROOT / "output" / today
outdir.mkdir(parents=True, exist_ok=True)
md = [f"# {brand} — 5 Haber Carousel ({today})\n"]
for i, c in enumerate(cards, 1):
    md.append(f"## Kart {i}: {c.get('title','')}\n")
    md.append(f"**Etiket:** {c.get('kick','')}\n\n{c.get('body','')}\n")
    md.append(f"_Kaynak: {c.get('source','')} — {c.get('link','')}_\n")
md.append("## Kart 6 (CTA): Founders & Investors Night\n")
md.append(f"\n**Caption:**\n\n{out['caption']}\n")
md.append(f"\n**Hashtagler:** {' '.join(out['hashtags'])}\n")
(outdir / "captions.md").write_text("\n".join(md), encoding="utf-8")

print(f"✓ {len(cards)} haber kartı üretildi:")
for i, c in enumerate(cards, 1):
    print(f"  {i}. {c.get('title','')[:60]}")
print(f"  Caption: output/{today}/captions.md")
