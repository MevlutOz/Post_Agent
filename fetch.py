"""
fetch.py — Kaynaklardan son N günün haberlerini toplar.
Çıktı: data/articles_raw.json
"""
import _bootstrap  # .env yükle + UTF-8 çıktı
import feedparser, yaml, json, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
cfg = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
lookback = cfg["settings"]["days_lookback"]
cutoff = datetime.now(timezone.utc) - timedelta(days=lookback)

def parse_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        if entry.get(key):
            return datetime.fromtimestamp(time.mktime(entry[key]), tz=timezone.utc)
    return None

articles = []
for feed in cfg["rss_feeds"]:
    print(f"  → {feed['name']} ...", end=" ")
    try:
        d = feedparser.parse(feed["url"])
        count = 0
        for e in d.entries:
            dt = parse_date(e)
            if dt and dt < cutoff:
                continue
            summary = e.get("summary", "") or e.get("description", "")
            # HTML etiketlerini kabaca temizle
            import re
            summary = re.sub(r"<[^>]+>", "", summary)[:600]
            articles.append({
                "source": feed["name"],
                "title": e.get("title", "").strip(),
                "link": e.get("link", ""),
                "summary": summary.strip(),
                "date": dt.isoformat() if dt else None,
            })
            count += 1
        print(f"{count} haber")
    except Exception as ex:
        print(f"HATA: {ex}")

# Tarihe göre yeni → eski sırala
articles.sort(key=lambda a: a["date"] or "", reverse=True)

out = ROOT / "data"
out.mkdir(exist_ok=True)
(out / "articles_raw.json").write_text(
    json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"\nToplam {len(articles)} haber toplandı (son {lookback} gün).")
print(f"Kaydedildi: data/articles_raw.json")
