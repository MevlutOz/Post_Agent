"""run_config.json okuma/yazma + tema seçimi ayrıştırma (saf)."""
import json
from pathlib import Path

_THEMES = {"1": "cta_mavi", "2": "editorial"}


def parse_theme_choice(s):
    return _THEMES.get((s or "").strip())


def save_run_config(theme, topic, path):
    Path(path).write_text(
        json.dumps({"theme": theme, "topic": topic}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_run_config(path):
    p = Path(path)
    if not p.exists():
        return {"theme": "cta_mavi", "topic": None}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {"theme": data.get("theme", "cta_mavi"), "topic": data.get("topic")}
