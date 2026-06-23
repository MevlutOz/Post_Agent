"""
wiro_client.py — Wiro AI görsel üretim istemcisi.

Akış: POST /Run/{owner}/{model} → taskid al → POST /Task/Detail ile poll et
      → çıktı görsel URL'ini döndür.

Kimlik doğrulama iki yöntemi de destekler:
  - API Key Only  : sadece WIRO_API_KEY  (x-api-key header)
  - Signature      : WIRO_API_KEY + WIRO_API_SECRET (HMAC-SHA256 imza)

Ortam değişkenleri:
  WIRO_API_KEY     (zorunlu)
  WIRO_API_SECRET  (signature yöntemi için)
  WIRO_MODEL       (varsayılan: "google/nano-banana-pro"; sources.yaml'dan da gelebilir)
"""
import os, time, hmac, hashlib, requests
from pathlib import Path

BASE = "https://api.wiro.ai/v1"


def _headers():
    api_key = os.environ.get("WIRO_API_KEY")
    if not api_key:
        raise RuntimeError("WIRO_API_KEY ortam değişkeni tanımlı değil.")
    secret = os.environ.get("WIRO_API_SECRET")
    h = {"x-api-key": api_key, "Content-Type": "application/json"}
    if secret:  # signature-based auth
        nonce = str(int(time.time()))
        sig = hmac.new(
            api_key.encode(), (secret + nonce).encode(), hashlib.sha256
        ).hexdigest()
        h["x-signature"] = sig
        h["x-nonce"] = nonce
    return h


def generate_image(prompt, model=None, width=1080, height=1080,
                   poll_interval=4, timeout=180):
    """
    Wiro'da bir görsel modeli çalıştırır, biten görselin URL'ini döndürür.
    model: "owner/model" formatında (örn. "google/nano-banana-pro").
    """
    model = model or os.environ.get("WIRO_MODEL", "google/nano-banana-pro")
    owner, name = model.split("/", 1)

    # 1) RUN
    payload = {"prompt": prompt, "width": width, "height": height}
    r = requests.post(f"{BASE}/Run/{owner}/{name}",
                      headers=_headers(), json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    if not data.get("result"):
        raise RuntimeError(f"Wiro Run hatası: {data.get('errors')}")
    taskid = data["taskid"]

    # 2) POLL  (Task/Detail)
    # Wiro durum akışı: task_queue → task_output → task_postprocess_end (bitti)
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(poll_interval)
        tr = requests.post(f"{BASE}/Task/Detail",
                           headers=_headers(), json={"taskid": taskid}, timeout=60)
        tr.raise_for_status()
        td = tr.json()
        tasks = td.get("tasklist") or td.get("task") or []
        task = tasks[0] if isinstance(tasks, list) and tasks else (tasks or {})
        status = (task or {}).get("status", "")

        # Başarısızlık: durum hata içeriyorsa ya da pexit sıfırdan farklıysa
        pexit = str(task.get("pexit", ""))
        if "error" in status or "fail" in status or (pexit not in ("", "0")):
            raise RuntimeError(f"Wiro görev hatası (status={status}, pexit={pexit}): "
                               f"{task.get('debugoutput') or task.get('errors')}")

        # SADECE görev tamamen bittiğinde (postprocess sonu) çıktı URL'ini al.
        # Ara durumlarda outputs geçici bir File/ URL'i içerebilir (404 verir);
        # nihai cdn URL'i postprocess sonunda gelir.
        if status == "task_postprocess_end":
            outputs = task.get("outputs") or []
            url = None
            if outputs and isinstance(outputs[0], dict):
                url = outputs[0].get("url")
            url = url or _extract_url(outputs)
            if url:
                return url
            raise RuntimeError(f"Görsel bitti ama çıktı URL'i bulunamadı: {task}")
    raise TimeoutError("Wiro görseli zaman aşımına uğradı.")


def _extract_url(obj):
    """Çıktı yapısından ilk görsel/dosya URL'ini bulmaya çalışır."""
    import re
    s = str(obj)
    m = re.search(r"https?://[^\s\"']+\.(?:png|jpg|jpeg|webp)", s)
    return m.group(0) if m else None


def download(url, dest: Path):
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest
