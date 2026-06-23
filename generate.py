"""
generate.py — Claude API: seçilen her haber için Instagram postu üretir
(başlık, caption, hashtag). Çıktı: data/posts.json + output/<tarih>/captions.md
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

curated = json.loads((ROOT / "data" / "curated.json").read_text(encoding="utf-8"))

posts = []
for c in curated:
    prompt = f"""Sen {brand} topluluğunun Instagram içerik yazarısın.
Marka tonu: bilgili ama samimi, kurucu-dostu, abartısız, Türkçe.
Hedef kitle: Türkiye'deki SaaS/AI kurucuları ve yatırımcılar.

Aşağıdaki haberden bir Instagram postu üret.

Haber başlığı: {c['title']}
Kaynak: {c['source']}
Özet: {c['summary']}
Önerilen açı: {c['angle']}

SADECE şu JSON formatında yanıt ver:
{{
  "visual_title": "<görsel kartın üstüne yazılacak çarpıcı kısa başlık, max 8 kelime, TR>",
  "visual_subtitle": "<görsel kartta alt satır, 1 kısa cümle, TR>",
  "caption": "<2-3 paragraf caption. Haberi açıkla, kurucuya 'ne anlama geliyor' bağla. Sonunda bir soru ile etkileşime davet et. Emoji ölçülü kullan>",
  "hashtags": ["#saas", "#yapayzeka", ...]  // 8-12 alakalı Türkçe+İngilizce hashtag
}}
"""
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(text)
    data["link"] = c["link"]
    data["source"] = c["source"]
    posts.append(data)
    print(f"  ✓ Post üretildi: {data['visual_title']}")

(ROOT / "data" / "posts.json").write_text(
    json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Okunabilir markdown çıktısı
today = date.today().isoformat()
outdir = ROOT / "output" / today
outdir.mkdir(parents=True, exist_ok=True)
md = [f"# {brand} — Haftalık Instagram Postları ({today})\n"]
for i, p in enumerate(posts, 1):
    md.append(f"## Post {i}: {p['visual_title']}\n")
    md.append(f"**Görsel alt başlık:** {p['visual_subtitle']}\n")
    md.append(f"**Kaynak:** {p['source']} — {p['link']}\n")
    md.append(f"**Caption:**\n\n{p['caption']}\n")
    md.append(f"**Hashtagler:** {' '.join(p['hashtags'])}\n")
    md.append("\n---\n")
(outdir / "captions.md").write_text("\n".join(md), encoding="utf-8")
print(f"\nCaption'lar yazıldı: output/{today}/captions.md")
