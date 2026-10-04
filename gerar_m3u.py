#!/usr/bin/env python3
"""
Brasil Stream Catalog v3
Ponto único de execução. NÃO depende de src/.
Uso:
    python gerar_m3u.py
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
CATALOGO_FILE = ROOT / "catalogo.json"
PLAYLIST_FILE = ROOT / "canais.m3u"
REPORT_FILE = ROOT / "relatorio.json"

BAD_NAMES = {
    "guia de programação", "guia de programacao",
    "programação", "programacao",
    "pg não informado", "pg nao informado",
    "não informado", "nao informado",
    "sem nome", "channel", "canal",
}

KEYWORDS = (
    "canal", "canais", "tv", "live", "ao-vivo", "aovivo",
    "assistir", "watch", "stream", "player", "play"
)

DIRECT_RE = re.compile(
    r"""https?://[^"'<>\s]+?\.(?:m3u8|mpd)(?:\?[^"'<>\s]*)?""",
    re.I,
)

YOUTUBE_RE = re.compile(
    r"""(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)
        ([A-Za-z0-9_-]{11})""",
    re.I | re.X,
)


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clean_name(name: str, fallback: str = "") -> str:
    name = re.sub(r"<[^>]+>", " ", name or "")
    name = re.sub(r"\s+", " ", name).strip(" -|•:")
    name = re.sub(r"\s+(?:ao vivo|live)\s*$", "", name, flags=re.I).strip()

    if not name or name.casefold() in BAD_NAMES:
        name = re.sub(r"\s+", " ", fallback or "").strip(" -|•:")

    if name.casefold() in BAD_NAMES:
        return ""

    return name


def canonical(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean_name(name).casefold())


def slug_name(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1] if path else ""
    return clean_name(slug.replace("-", " ").replace("_", " ").title())


def extract_page_name(html: str, url: str) -> str:
    patterns = [
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)',
        r"<h1[^>]*>(.*?)</h1>",
        r"<title[^>]*>(.*?)</title>",
    ]

    for pattern in patterns:
        match = re.search(pattern, html or "", re.I | re.S)
        if not match:
            continue
        candidate = clean_name(match.group(1))
        if candidate:
            return candidate

    return slug_name(url)


def extract_direct_streams(html: str, base_url: str):
    found = []
    for url in DIRECT_RE.findall(html or ""):
        url = urljoin(base_url, url)
        if url not in found:
            found.append(url)
    return found


def extract_youtube_streams(html: str):
    found = []
    for video_id in YOUTUBE_RE.findall(html or ""):
        url = f"https://www.youtube.com/watch?v={video_id}"
        if url not in found:
            found.append(url)
    return found


def should_follow(url: str, text: str = "") -> bool:
    value = f"{url} {text}".casefold()
    return any(keyword in value for keyword in KEYWORDS)


def validate_stream(url: str, timeout: int) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.casefold()

    # YouTube oficial: a página é o endereço público do player.
    if "youtube.com" in host or "youtu.be" in host:
        return True

    try:
        import requests

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Range": "bytes=0-1024",
            },
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
        return response.status_code < 500
    except Exception:
        return False


async def crawl_source(browser, source, settings):
    start_url = source["url"]
    max_pages = int(settings.get("max_pages_per_source", 60))
    timeout_ms = int(settings.get("browser_timeout_ms", 30000))
    wait_ms = int(settings.get("render_wait_ms", 1000))
    allow_youtube = bool(settings.get("allow_youtube", True))

    domain = urlparse(start_url).netloc.casefold()
    queue = [start_url]
    seen = set()
    records = []

    page = await browser.new_page(
        user_agent=settings.get(
            "user_agent",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "Chrome/140 Safari/537.36",
        )
    )

    try:
        while queue and len(seen) < max_pages:
            url = queue.pop(0)

            if url in seen:
                continue

            seen.add(url)

            try:
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=timeout_ms,
                )
                await page.wait_for_timeout(wait_ms)
                html = await page.content()
            except Exception as exc:
                print(f"  AVISO página: {url} -> {exc}")
                continue

            name = extract_page_name(html, url)
            streams = extract_direct_streams(html, url)

            if streams and name:
                records.append({
                    "name": name,
                    "category": source.get("category", "TV"),
                    "source": source["name"],
                    "page": url,
                    "stream": streams[0],
                    "stream_type": "hls/mpd",
                })

            if allow_youtube and not streams:
                youtube = extract_youtube_streams(html)
                if youtube and name:
                    records.append({
                        "name": name,
                        "category": source.get("category", "TV"),
                        "source": source["name"],
                        "page": url,
                        "stream": youtube[0],
                        "stream_type": "youtube",
                    })

            try:
                links = await page.locator("a[href]").all()
                for link in links:
                    href = await link.get_attribute("href")
                    if not href:
                        continue

                    text = ""
                    try:
                        text = await link.inner_text()
                    except Exception:
                        pass

                    child = urljoin(url, href)

                    if urlparse(child).netloc.casefold() != domain:
                        continue

                    if child in seen:
                        continue

                    if should_follow(child, text):
                        queue.append(child)

            except Exception:
                pass

    finally:
        await page.close()

    return records


def merge_records(records):
    merged = {}

    for record in records:
        name = clean_name(record.get("name", ""))
        stream = record.get("stream", "")

        if not name or not stream:
            continue

        key = canonical(name)

        if not key:
            continue

        if key not in merged:
            record["name"] = name
            merged[key] = record

    return list(merged.values())


def preserve_previous(previous, current):
    merged = {}

    for record in previous:
        key = canonical(record.get("name", ""))
        if key:
            merged[key] = record

    # Atualizações atuais têm prioridade sobre registros antigos.
    for record in current:
        key = canonical(record.get("name", ""))
        if key:
            merged[key] = record

    return list(merged.values())


def write_m3u(records):
    lines = ["#EXTM3U"]

    for record in sorted(
        records,
        key=lambda item: (
            item.get("category", "TV").casefold(),
            item["name"].casefold(),
        ),
    ):
        name = record["name"].replace('"', "'")
        category = (record.get("category") or "TV").replace('"', "'")
        logo = record.get("logo", "")

        logo_field = f' tvg-logo="{logo}"' if logo else ""

        lines.append(
            f'#EXTINF:-1 tvg-name="{name}" '
            f'group-title="{category}"{logo_field},{name}'
        )
        lines.append(record["stream"])

    PLAYLIST_FILE.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


async def collect_all(sources, settings):
    from playwright.async_api import async_playwright

    records = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        try:
            for source in sources:
                print()
                print(f"Fonte: {source['name']}")
                print(f"URL:   {source['url']}")

                before = len(records)

                try:
                    found = await crawl_source(
                        browser,
                        source,
                        settings,
                    )
                    records.extend(found)
                    print(f"Encontrados nesta fonte: {len(found)}")
                except Exception as exc:
                    print(f"ERRO na fonte: {exc}")

                print(f"Total acumulado: {len(records)}")
        finally:
            await browser.close()

    return records


def run():
    print("=== BRASIL STREAM CATALOG v3 ===")

    settings = load_json(
        CONFIG_DIR / "settings.json",
        {},
    )
    sources = load_json(
        CONFIG_DIR / "sources.json",
        [],
    )
    previous = load_json(
        CATALOGO_FILE,
        [],
    )

    if not sources:
        print("ERRO: config/sources.json está vazio.")
        return 2

    try:
        collected = asyncio.run(
            collect_all(sources, settings)
        )
    except Exception as exc:
        print()
        print("ERRO GERAL DE COLETA:", exc)
        collected = []

    current = merge_records(collected)

    timeout = int(settings.get("stream_timeout", 10))

    print()
    print(f"Registros descobertos: {len(current)}")

    valid = []

    for record in current:
        if validate_stream(record["stream"], timeout):
            valid.append(record)

    print(f"Transmissões consideradas válidas: {len(valid)}")

    minimum = int(
        settings.get(
            "minimum_channels_to_publish",
            5,
        )
    )

    # Regra de segurança:
    # nunca apagar uma playlist existente por causa de uma falha temporária.
    if len(valid) < minimum:
        if previous:
            print(
                f"COLETA INSUFICIENTE: {len(valid)} < {minimum}."
            )
            print("Playlist anterior preservada.")

            save_json(
                REPORT_FILE,
                {
                    "status": "preserved",
                    "discovered": len(current),
                    "valid": len(valid),
                    "published": len(previous),
                },
            )
            return 0

        print(
            "ERRO: primeira coleta não encontrou a quantidade mínima "
            "de transmissões válidas."
        )
        print("Nenhuma playlist será publicada.")
        return 3

    published = preserve_previous(previous, valid)

    save_json(CATALOGO_FILE, published)
    write_m3u(published)

    save_json(
        REPORT_FILE,
        {
            "status": "updated",
            "discovered": len(current),
            "valid": len(valid),
            "published": len(published),
        },
    )

    print()
    print(f"SUCESSO: {len(published)} canais publicados.")
    print(f"Playlist: {PLAYLIST_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
