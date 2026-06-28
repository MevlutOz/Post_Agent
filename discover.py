"""discover.py — verilen konuyu Claude + web_search ile güncel haber adaylarına
çevirip data/articles_raw.json'a yazar (fetch.py ile aynı şema)."""
import _bootstrap  # noqa: F401
import json
import sys
from pathlib import Path
import anthropic
from anthropic import Anthropic

from runconfig import load_run_config

ROOT = Path(__file__).resolve().parent

ARTICLE_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["articles"],
        "properties": {
            "articles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["source", "title", "link", "summary", "date"],
                    "properties": {
                        "source": {"type": "string"},
                        "title": {"type": "string"},
                        "link": {"type": "string"},
                        "summary": {"type": "string"},
                        "date": {"type": "string"},
                    },
                },
            }
        },
    },
}


def build_search_prompt(topic, max_n, brand):
    return (
        f"Sen {brand} adlı Türkiye SaaS & AI topluluğunun haber editörüsün.\n"
        f"Konu: \"{topic}\".\n"
        f"web_search aracını kullanarak bu konuyla ilgili EN GÜNCEL, güvenilir "
        f"ve ilgi çekici en fazla {max_n} haber bul. Hedef kitle: SaaS/AI "
        f"kurucuları ve yatırımcıları. Magazinsel/alakasız olanları ele.\n"
        f"Her haber için kaynağın adını, başlığı, gerçek URL'yi, 1-2 cümlelik "
        f"özeti ve yayın tarihini (ISO 8601, bilinmiyorsa boş) ver.\n"
        f"SADECE şemaya uygun JSON döndür."
    )


def _parse_articles_from_text(text, max_n):
    """Parse JSON from text block, stripping ```json fences if present."""
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)["articles"][:max_n]


def main():
    cfg = load_run_config(ROOT / "data" / "run_config.json")
    topic = cfg.get("topic")
    if not topic:
        raise SystemExit("discover.py: run_config.json'da topic yok.")

    import yaml
    settings = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))["settings"]
    max_n = settings.get("max_candidates", 15)
    brand = settings.get("brand_name") or sys.exit("sources.yaml'da brand_name yok")

    client = Anthropic()
    prompt = build_search_prompt(topic, max_n, brand)

    # Primary attempt: output_config.format + web_search
    try:
        resp = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=8000,
            thinking={"type": "adaptive"},
            tools=[{"type": "web_search_20260209", "name": "web_search",
                    "max_uses": 8}],
            output_config={"format": ARTICLE_SCHEMA},
            messages=[{"role": "user", "content": prompt}],
        )
        text = next((b.text for b in resp.content if b.type == "text"), "")
        if not text:
            raise ValueError("Yanıtta metin bloğu yok")
        articles = _parse_articles_from_text(text, max_n)

    except (anthropic.BadRequestError, json.JSONDecodeError, ValueError) as e:
        # Fallback: drop output_config.format; append explicit JSON instruction to prompt
        print(f"[discover] Birincil çağrı başarısız ({type(e).__name__}: {e}). "
              f"Fallback (output_config olmadan) deneniyor...")
        fallback_prompt = (
            prompt
            + "\n\nSADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:\n"
            + '{"articles": [{"source": "...", "title": "...", "link": "...", '
            + '"summary": "...", "date": "..."}]}'
        )
        resp = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=8000,
            thinking={"type": "adaptive"},
            tools=[{"type": "web_search_20260209", "name": "web_search",
                    "max_uses": 8}],
            messages=[{"role": "user", "content": fallback_prompt}],
        )
        text = next((b.text for b in resp.content if b.type == "text"), "")
        if not text:
            raise SystemExit("discover.py: Fallback yanıtında da metin bloğu yok.")
        articles = _parse_articles_from_text(text, max_n)

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "articles_raw.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✓ '{topic}' için {len(articles)} haber bulundu → data/articles_raw.json")
    for i, a in enumerate(articles, 1):
        print(f"  {i}. {a['title'][:70]}")


if __name__ == "__main__":
    main()
