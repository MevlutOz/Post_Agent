"""
curate.py — Claude API: toplanan haberlerden en alakalı ~N adayı seçip
sıralar ve her birine kısa 'neden ilgi çekici' + 'önerilen açı' ekler.
Otomatik post ÜRETMEZ; sadece kullanıcıya sunulacak aday listesini hazırlar.
Çıktı: data/candidates.json
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import json, yaml
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).parent
cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
client = Anthropic()  # ANTHROPIC_API_KEY ortam değişkeninden okunur

articles = json.loads((ROOT / "data" / "articles_raw.json").read_text(encoding="utf-8"))
articles = articles[: cfg["settings"]["max_articles_to_claude"]]

max_candidates = cfg["settings"].get("max_candidates", 15)
brand = cfg["settings"]["brand_name"]

listing = "\n".join(
    f"[{i}] ({a['source']}) {a['title']} — {a['summary'][:200]}"
    for i, a in enumerate(articles)
)

prompt = f"""Sen {brand} adlı, Türkiye SaaS & AI ekosistemine odaklanan bir
topluluğun içerik editörüsün. Aşağıda son 1 haftanın haber başlıkları var.

Hedef kitle: kurucular, yatırımcılar, SaaS/AI girişimcileri.
Konular: SaaS, AI, AI agent, girişimcilik, yatırım/VC.

Görevin: Bu listeden Instagram'da paylaşmaya EN değer en fazla {max_candidates}
haberi seç ve EN ilgi çekiciden aza doğru SIRALA. Magazinsel/alakasız olanları ele.
Kriterler: güncellik, ekosisteme alaka, kurucuların ilgisini çekme, özgünlük.

SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{{
  "candidates": [
    {{"index": <haber no>, "reason": "<neden ilgi çekici, 1 cümle TR>", "angle": "<post için açı/vurgu, 1 cümle TR>"}}
  ]
}}

Haberler:
{listing}
"""

resp = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=2500,
    messages=[{"role": "user", "content": prompt}],
)
text = resp.content[0].text.strip()
text = text.replace("```json", "").replace("```", "").strip()
sel = json.loads(text)["candidates"]

candidates = []
for s in sel:
    i = s["index"]
    if not (0 <= i < len(articles)):
        continue
    art = articles[i]
    candidates.append({**art, "reason": s["reason"], "angle": s["angle"]})

(ROOT / "data" / "candidates.json").write_text(
    json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"{len(candidates)} aday haber hazırlandı:")
for i, c in enumerate(candidates, 1):
    print(f"  {i}. {c['title'][:70]}")
