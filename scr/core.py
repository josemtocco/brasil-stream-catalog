from __future__ import annotations
import asyncio, json, re
from pathlib import Path
from .normalize import canonical, clean_name
from .sources import crawl_browser
from .validate import validate_stream

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"config"
CATALOGO=ROOT/"catalogo.json"
PLAYLIST=ROOT/"canais.m3u"
REPORT=ROOT/"relatorio.json"

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

async def collect(sources, settings):
    from playwright.async_api import async_playwright
    all_records=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page(user_agent=settings.get("user_agent","Mozilla/5.0"))
        for source in sources:
            print(f"Fonte: {source['name']} -> {source['url']}")
            before=len(all_records)
            try:
                all_records.extend(await crawl_browser(page,source,settings))
            except Exception as exc:
                print("  ERRO:",exc)
            print("  registros:",len(all_records)-before)
        await browser.close()
    return all_records

def merge(records):
    out={}
    for r in records:
        n=clean_name(r.get("name",""))
        s=r.get("stream","")
        if not n or not s:
            continue
        key=canonical(n)
        if key and key not in out:
            r["name"]=n
            out[key]=r
    return list(out.values())

def preserve_previous(old, current):
    by={canonical(x.get("name","")):x for x in current}
    for r in old:
        k=canonical(r.get("name",""))
        if k and k not in by:
            by[k]=r
    return list(by.values())

def write_m3u(records):
    lines=["#EXTM3U"]
    for r in sorted(records,key=lambda x:(x.get("category","TV"),x["name"].casefold())):
        name=r["name"].replace('"',"'")
        cat=(r.get("category") or "TV").replace('"',"'")
        logo=r.get("logo","")
        extra=f' tvg-logo="{logo}"' if logo else ""
        lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="{cat}"{extra},{name}')
        lines.append(r["stream"])
    PLAYLIST.write_text("\\n".join(lines)+"\\n",encoding="utf-8")

def run():
    settings=load(CONFIG/"settings.json",{})
    sources=load(CONFIG/"sources.json",[])
    old=load(CATALOGO,[])
    if not sources:
        print("ERRO: fontes não configuradas")
        return 2
    try:
        raw=asyncio.run(collect(sources,settings))
    except Exception as exc:
        print("ERRO GERAL:",exc)
        raw=[]
    current=merge(raw)
    validated=[r for r in current if validate_stream(r["stream"],int(settings.get("stream_timeout",10)))]

    minimum=int(settings.get("minimum_channels_to_publish",5))
    if len(validated)<minimum:
        if old:
            print(f"COLETA INSUFICIENTE: {len(validated)} < {minimum}. Playlist anterior preservada.")
            REPORT.write_text(json.dumps({"status":"preserved","current":len(validated),
                                          "published":len(old)},ensure_ascii=False,indent=2),encoding="utf-8")
            return 0
        if not validated:
            print("ERRO: nenhuma transmissão válida encontrada; playlist não será substituída.")
            return 3

    published=preserve_previous(old,validated)
    CATALOGO.write_text(json.dumps(published,ensure_ascii=False,indent=2),encoding="utf-8")
    write_m3u(published)
    REPORT.write_text(json.dumps({"status":"updated","found":len(current),
                                  "validated":len(validated),"published":len(published)},
                                 ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"OK: {len(published)} canais publicados.")
    return 0
