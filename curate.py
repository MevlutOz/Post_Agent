"""
curate.py — Claude API: toplanan haberlerden en alakalı / paylaşıma değer
olanları seçer ve neden seçildiğini açıklar.
Çıktı: data/curated.json
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import json, yaml, os
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).parent
cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
client = Anthropic()  # ANTHROPIC_API_KEY ortam değişkeninden okunur

articles = json.loads((ROOT / "data" / "articles_raw.json").read_text(encoding="utf-8"))
articles = articles[: cfg["settings"]["max_articles_to_claude"]]

# Claude'a kısa liste ver
listing = "\n".join(
    f"[{i}] ({a['source']}) {a['title']} — {a['summary'][:200]}"
    for i, a in enumerate(articles)
)

num = cfg["settings"]["num_posts"]
brand = cfg["settings"]["brand_name"]

prompt = f"""Sen {brand} adlı, Türkiye SaaS & AI ekosistemine odaklanan bir
topluluğun içerik editörüsün. Aşağıda son 1 haftanın haber başlıkları var.

Hedef kitle: kurucular, yatırımcılar, SaaS/AI girişimcileri.
Konular: SaaS, AI, AI agent, girişimcilik, yatırım/VC.

Görevin: Bu listeden Instagram'da paylaşmaya EN değer {num} haberi seç.
Kriterler: güncellik, ekosisteme alaka, kurucuların ilgisini çekme, özgünlük.
Magazinsel/alakasız olanları ele.

SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{{
  "selected": [
    {{"index": <haber no>, "reason": "<neden seçtiğin, 1 cümle TR>", "angle": "<post için açı/vurgu, 1 cümle TR>"}}
  ]
}}

Haberler:
{listing}
"""

resp = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=1500,
    messages=[{"role": "user", "content": prompt}],
)
text = resp.content[0].text.strip()
# olası ```json fence temizliği
text = text.replace("```json", "").replace("```", "").strip()
sel = json.loads(text)["selected"]

curated = []
for s in sel:
    art = articles[s["index"]]
    curated.append({**art, "reason": s["reason"], "angle": s["angle"]})

(ROOT / "data" / "curated.json").write_text(
    json.dumps(curated, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"{len(curated)} haber seçildi:")
for c in curated:
    print(f"  • {c['title'][:70]}  →  {c['reason']}")
