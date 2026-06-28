import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runconfig import parse_theme_choice, save_run_config, load_run_config


def test_parse_theme_choice():
    assert parse_theme_choice("1") == "cta_mavi"
    assert parse_theme_choice("2") == "editorial"
    assert parse_theme_choice("  2 ") == "editorial"
    assert parse_theme_choice("3") is None
    assert parse_theme_choice("") is None
    assert parse_theme_choice("abc") is None


def test_save_and_load_round_trip(tmp_path):
    p = tmp_path / "run_config.json"
    save_run_config("editorial", "Dünya Kupası SaaS", p)
    cfg = load_run_config(p)
    assert cfg == {"theme": "editorial", "topic": "Dünya Kupası SaaS"}


def test_save_none_topic(tmp_path):
    p = tmp_path / "run_config.json"
    save_run_config("cta_mavi", None, p)
    assert json.loads(p.read_text(encoding="utf-8"))["topic"] is None


def test_load_missing_file_defaults(tmp_path):
    cfg = load_run_config(tmp_path / "yok.json")
    assert cfg == {"theme": "cta_mavi", "topic": None}
