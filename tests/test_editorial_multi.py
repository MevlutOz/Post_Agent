# tests/test_editorial_multi.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import wiro_client
from themes.editorial_multi import _generate_cover_photo

COVER = {"title": "Başlık", "image_subject": "world cup trophy in a stadium"}


def test_cover_photo_generated_via_wiro(tmp_path, monkeypatch):
    calls = {}

    def fake_generate(prompt, model=None, width=None, height=None):
        calls["prompt"] = prompt
        return "http://example/img.png"

    def fake_download(url, dest):
        Path(dest).write_bytes(b"png")

    monkeypatch.setattr(wiro_client, "generate_image", fake_generate)
    monkeypatch.setattr(wiro_client, "download", fake_download)
    name = _generate_cover_photo(COVER, tmp_path, "test-model")
    assert name == "_cover.png"
    assert (tmp_path / "_cover.png").exists()
    assert "world cup trophy" in calls["prompt"]


def test_cover_photo_reused_if_exists(tmp_path, monkeypatch):
    (tmp_path / "_cover.png").write_bytes(b"eski")

    def boom(*a, **k):
        raise AssertionError("Wiro çağrılmamalıydı")

    monkeypatch.setattr(wiro_client, "generate_image", boom)
    name = _generate_cover_photo(COVER, tmp_path, "test-model")
    assert name == "_cover.png"
    assert (tmp_path / "_cover.png").read_bytes() == b"eski"


def test_cover_photo_failure_writes_placeholder(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("api down")

    monkeypatch.setattr(wiro_client, "generate_image", boom)
    name = _generate_cover_photo(COVER, tmp_path, "test-model")
    assert name == "_cover.png"
    assert (tmp_path / "_cover.png").stat().st_size > 0  # placeholder yazıldı
