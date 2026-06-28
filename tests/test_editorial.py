# tests/test_editorial.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from themes.editorial import photo_subjects

POST = {
    "cover_title": "Menlo Ventures 3 milyar dolarlık fonunu kapattı",
    "slides": [
        {"heading": "Ne oldu?", "body": "..."},
        {"heading": "Neden önemli?", "body": "..."},
        {"heading": "Kuruculara ne anlama geliyor?", "body": "..."},
    ],
}


def test_photo_subjects_keys_and_nonempty():
    subj = photo_subjects(POST)
    assert set(subj.keys()) == {"hero", "move", "founder", "investor"}
    assert all(subj.values())
    assert "Menlo" in subj["hero"]
