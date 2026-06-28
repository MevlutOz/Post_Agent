# run.py
"""run.py — Tüm pipeline'ı tek komutla çalıştırır.
Başta tasarım teması (editöryelde ayrıca konu) sorulur.
Kullanım:  python run.py  (ya da çift tık: calistir.bat)"""
import _bootstrap  # noqa: F401
import subprocess, sys
from pathlib import Path

from runconfig import parse_theme_choice, save_run_config

ROOT = Path(__file__).resolve().parent


def ask_setup():
    print("Hangi tasarım? 1) CTA Mavi (mevcut)   2) Editöryel (Menlo/WIRED)")
    theme = None
    while theme is None:
        theme = parse_theme_choice(input("Seçim (1/2): "))
        if theme is None:
            print("Lütfen 1 ya da 2 gir.")
    topic = None
    if theme == "editorial":
        topic = input("Konu gir (boş = haftalık RSS taraması): ").strip() or None
    save_run_config(theme, topic, ROOT / "data" / "run_config.json")
    return theme, topic


def main():
    (ROOT / "data").mkdir(exist_ok=True)
    theme, topic = ask_setup()

    fetch_step = ("1/5  Konuya göre haberler aranıyor (web)", "discover.py") if topic \
        else ("1/5  Haberler toplanıyor (RSS)", "fetch.py")
    steps = [
        fetch_step,
        ("2/5  Claude aday haberleri hazırlıyor", "curate.py"),
        ("3/5  Haber seçimi (sen seçeceksin)", "secim.py"),
        ("4/5  Claude carousel metni üretiyor", "generate.py"),
        ("5/5  Slayt görselleri hazırlanıyor", "make_image.py"),
    ]
    for label, script in steps:
        print(f"\n{'='*50}\n{label}\n{'='*50}", flush=True)
        if subprocess.run([sys.executable, str(ROOT / script)]).returncode != 0:
            print(f"\n✗ Hata: {script} adımında durdu.")
            sys.exit(1)

    print("\n✅ Bitti. Çıktılar output/<tarih>/ klasöründe "
          "(captions.md + slide_1..N.png)")


if __name__ == "__main__":
    main()
