import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from .sources import SourceCrawler
from .normalize import canonical_name, clean_text, valid_name, infer_category
from .validate import validate_stream

LOG = logging.getLogger(__name__)

def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def merge_records(records):
    grouped = {}
    for r in records:
        if not valid_name(r.get("name", "")):
            continue
        key = canonical_name(r["name"])
        if key not in grouped:
            grouped[key] = {
                "name": clean_text(r["name"]),
                "category": r.get("category") or infer_category(r["name"]),
                "page_url": r.get("page_url", ""),
                "sources": [],
                "streams": [],
                "official_hint": False,
                "last_seen": datetime.now(timezone.utc).isoformat()
            }
        g = grouped[key]
        if r.get("source_name") and r["source_name"] not in g["sources"]:
            g["sources"].append(r["source_name"])
        for stream in r.get("streams", []):
            if stream not in g["streams"]:
                g["streams"].append(stream)
        g["official_hint"] = g["official_hint"] or bool(r.get("official_hint"))
        if not g["page_url"]:
            g["page_url"] = r.get("page_url", "")
    return list(grouped.values())

def validate_records(records, settings):
    if not settings.get("validate_streams", True):
        for r in records:
            r["active"] = None
        return records

    def one(item):
        checked = []
        for stream in item.get("streams", [])[:10]:
            result = validate_stream(stream, settings["stream_timeout"], settings["user_agent"])
            checked.append({"url": stream, **result})
        item["checks"] = checked
        item["active"] = any(x["ok"] for x in checked)
        item["streams"] = [x["url"] for x in checked if x["ok"]] or item.get("streams", [])
        return item

    with ThreadPoolExecutor(max_workers=settings["max_workers"]) as ex:
        futures = [ex.submit(one, r) for r in records]
        return [f.result() for f in as_completed(futures)]

def write_m3u(records, path):
    lines = ["#EXTM3U"]
    for r in sorted(records, key=lambda x: (x.get("category", "Outros"), x.get("name", ""))):
        streams = r.get("streams", [])
        if not streams:
            continue
        stream = streams[0]
        if stream.lower().endswith(".mpd"):
            # Mantém no catálogo, mas não publica como M3U tradicional.
            continue
        name = clean_text(r["name"]).replace('"', "'")
        cat = clean_text(r.get("category", "Outros")).replace('"', "'")
        lines.append(f'#EXTINF:-1 group-title="{cat}",{name}')
        lines.append(stream)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def run(root):
    settings = load_json(root / "config/settings.json", {})
    sources = load_json(root / "config/sources.json", [])
    old = load_json(root / "catalogo.json", [])

    enabled = [s for s in sources if s.get("enabled")]
    all_records = []

    for source in enabled:
        LOG.info("Fonte: %s", source["name"])
        try:
            found = SourceCrawler(source, settings).crawl()
            LOG.info("%s: %d registros", source["name"], len(found))
            all_records.extend(found)
        except Exception:
            LOG.exception("Falha na fonte %s", source["name"])

    merged = merge_records(all_records)

    if merged:
        merged = validate_records(merged, settings)

    active = [r for r in merged if r.get("active") is True or (not settings.get("validate_streams", True) and r.get("streams"))]

    # Proteção contra uma execução vazia/defeituosa.
    if len(active) < settings.get("minimum_channels_to_publish", 5):
        LOG.warning("Coleta insuficiente (%d canais ativos). Catálogo anterior preservado.", len(active))
        return {
            "published": False,
            "channels_found": len(merged),
            "channels_active": len(active),
            "reason": "minimum_channels_to_publish_not_reached"
        }

    now = datetime.now(timezone.utc).isoformat()
    for r in merged:
        r["updated_at"] = now

    save_json(root / "catalogo.json", merged)
    write_m3u(active, root / "canais.m3u")

    report = {
        "generated_at": now,
        "sources": len(enabled),
        "raw_records": len(all_records),
        "unique_channels": len(merged),
        "active_channels": len(active),
        "inactive_channels": len(merged) - len(active),
        "categories": {},
        "published": True
    }
    for r in active:
        c = r.get("category", "Outros")
        report["categories"][c] = report["categories"].get(c, 0) + 1

    save_json(root / "relatorio.json", report)
    return report
