import json
import sys
from pathlib import Path
import requests

root = Path(__file__).resolve().parents[1]
sources = json.loads((root / "config/sources.json").read_text(encoding="utf-8"))
settings = json.loads((root / "config/settings.json").read_text(encoding="utf-8"))

for source in sources:
    if not source.get("enabled"):
        continue
    for url in source.get("start_urls", []):
        try:
            r = requests.get(
                url,
                timeout=settings["request_timeout"],
                headers={"User-Agent": settings["user_agent"]},
                allow_redirects=True,
            )
            print(f"[{'OK' if r.status_code < 400 else 'ERRO'}] {source['name']}: {r.status_code} {url}")
        except Exception as exc:
            print(f"[ERRO] {source['name']}: {url} -> {exc}")
