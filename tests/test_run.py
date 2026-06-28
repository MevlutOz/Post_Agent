"""tests/test_run.py — run.py yönlendirme (routing) testleri.

subprocess.run ve builtins.input monkeypatched edilir;
gerçek pipeline adımları çalıştırılmaz.
"""
import sys, json, types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import run  # noqa: E402 — side-effect-free at import time (guarded by __main__)


# ---------------------------------------------------------------------------
# Yardımcı: sahte subprocess.run kaydedici
# ---------------------------------------------------------------------------
class _FakeResult:
    returncode = 0


def _make_fake_subprocess(captured_scripts: list):
    """Her çağrıda betiği kaydeden sahte subprocess.run döndürür."""

    def fake_run(cmd, **kwargs):
        # cmd = [sys.executable, "/abs/path/script.py"]
        captured_scripts.append(Path(cmd[1]).name)
        return _FakeResult()

    return fake_run


# ---------------------------------------------------------------------------
# Test 1: Editöryel tema + konu → discover.py
# ---------------------------------------------------------------------------
def test_editorial_with_topic_routes_to_discover(tmp_path, monkeypatch):
    cfg_file = tmp_path / "run_config.json"

    # ROOT'u geçici dizine yönlendir (data/ mkdir + run_config.json yazımı için)
    monkeypatch.setattr(run, "ROOT", tmp_path)
    # data/ alt dizini gerekli çünkü main() onu yaratır
    # (tmp_path zaten var; mkdir exist_ok=True ile çalışır)

    # Kullanıcı cevapları: tema=2 (editorial), konu="AI ajanları"
    inputs = iter(["2", "AI ajanları"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    # save_run_config'in yazdığı path'i geçici yere çevir
    import runconfig as _rc

    def patched_save(theme, topic, path):
        _rc.save_run_config.__wrapped__ if hasattr(_rc.save_run_config, "__wrapped__") else None
        # orijinal fonksiyonu geçici path'e yönlendir
        _rc.save_run_config.__class__  # no-op; call original with tmp path
        import json as _json
        Path(cfg_file).write_text(
            _json.dumps({"theme": theme, "topic": topic}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    monkeypatch.setattr(run, "save_run_config", patched_save)

    # subprocess.run sahte — betik isimlerini kaydeder
    captured = []
    monkeypatch.setattr(run.subprocess, "run", _make_fake_subprocess(captured))

    run.main()

    # İlk adım discover.py olmalı
    assert captured[0] == "discover.py", f"Beklenen discover.py, gelen {captured[0]}"
    # Toplam 5 adım
    assert len(captured) == 5
    assert captured[1:] == ["curate.py", "secim.py", "generate.py", "make_image.py"]

    # run_config.json doğru yazılmalı
    data = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert data["theme"] == "editorial"
    assert data["topic"] == "AI ajanları"


# ---------------------------------------------------------------------------
# Test 2: CTA Mavi tema → fetch.py, topic=None
# ---------------------------------------------------------------------------
def test_cta_mavi_routes_to_fetch(tmp_path, monkeypatch):
    cfg_file = tmp_path / "run_config.json"

    monkeypatch.setattr(run, "ROOT", tmp_path)

    # Kullanıcı cevabı: tema=1 (cta_mavi) — konu sorusu gelMEZ
    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    import runconfig as _rc

    def patched_save(theme, topic, path):
        import json as _json
        Path(cfg_file).write_text(
            _json.dumps({"theme": theme, "topic": topic}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    monkeypatch.setattr(run, "save_run_config", patched_save)

    captured = []
    monkeypatch.setattr(run.subprocess, "run", _make_fake_subprocess(captured))

    run.main()

    assert captured[0] == "fetch.py", f"Beklenen fetch.py, gelen {captured[0]}"
    assert len(captured) == 5

    data = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert data["theme"] == "cta_mavi"
    assert data["topic"] is None


# ---------------------------------------------------------------------------
# Test 3: Geçersiz giriş → döngü, sonra geçerli seçim
# ---------------------------------------------------------------------------
def test_invalid_then_valid_input_loops(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "ROOT", tmp_path)

    # "x" geçersiz, sonra "1" geçerli
    inputs = iter(["x", "abc", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    import runconfig as _rc

    def patched_save(theme, topic, path):
        import json as _json
        (tmp_path / "data").mkdir(exist_ok=True)
        (tmp_path / "run_config.json").write_text(
            _json.dumps({"theme": theme, "topic": topic}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    monkeypatch.setattr(run, "save_run_config", patched_save)

    captured = []
    monkeypatch.setattr(run.subprocess, "run", _make_fake_subprocess(captured))

    run.main()

    # Sonunda cta_mavi ile fetch.py seçilmeli
    assert captured[0] == "fetch.py"


# ---------------------------------------------------------------------------
# Test 4: Editöryel + boş konu → RSS (fetch.py) yolu
# ---------------------------------------------------------------------------
def test_editorial_empty_topic_routes_to_fetch(tmp_path, monkeypatch):
    cfg_file = tmp_path / "run_config.json"
    monkeypatch.setattr(run, "ROOT", tmp_path)

    # tema=2, konu boş bırakıldı
    inputs = iter(["2", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    import runconfig as _rc

    def patched_save(theme, topic, path):
        import json as _json
        Path(cfg_file).write_text(
            _json.dumps({"theme": theme, "topic": topic}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    monkeypatch.setattr(run, "save_run_config", patched_save)

    captured = []
    monkeypatch.setattr(run.subprocess, "run", _make_fake_subprocess(captured))

    run.main()

    # Boş konu → topic=None → fetch.py
    assert captured[0] == "fetch.py"
    data = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert data["theme"] == "editorial"
    assert data["topic"] is None
