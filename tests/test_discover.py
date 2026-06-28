import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from discover import build_search_prompt, ARTICLE_SCHEMA


def test_prompt_contains_topic_and_count():
    p = build_search_prompt("Dünya Kupası SaaS ve AI", 15, "SaaS Bridge")
    assert "Dünya Kupası SaaS ve AI" in p
    assert "15" in p
    assert "SaaS Bridge" in p


def test_schema_shape():
    props = ARTICLE_SCHEMA["schema"]["properties"]
    item = props["articles"]["items"]["properties"]
    assert set(item.keys()) == {"source", "title", "link", "summary", "date"}
    assert ARTICLE_SCHEMA["schema"]["additionalProperties"] is False
