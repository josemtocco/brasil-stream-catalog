from urllib.parse import urlparse, urljoin
from .extract import direct_streams, youtube_urls, page_name

KEYWORDS=("canal","tv","live","ao-vivo","assistir","watch","stream","play")

def discover_from_html(html, url, source, allow_youtube=True):
    records=[]
    name=page_name(html,url)
    streams=direct_streams(html,url)
    if streams:
        records.append({"name":name,"category":source.get("category","TV"),
                        "source":source["name"],"page":url,
                        "stream":streams[0],"stream_type":"hls/mpd"})
    elif allow_youtube:
        yt=youtube_urls(html,url)
        if yt:
            records.append({"name":name,"category":source.get("category","TV"),
                            "source":source["name"],"page":url,
                            "stream":yt[0],"stream_type":"youtube"})
    return records

def should_follow(url, text=""):
    s=(url+" "+text).casefold()
    return any(k in s for k in KEYWORDS)

async def crawl_browser(page, source, settings):
    start=source["url"]
    max_pages=int(settings.get("max_pages_per_source",80))
    allow_youtube=bool(settings.get("allow_youtube",True))
    domain=urlparse(start).netloc
    queue=[start]; seen=set(); records=[]
    while queue and len(seen)<max_pages:
        url=queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            await page.goto(url, wait_until="domcontentloaded",
                            timeout=int(settings.get("browser_timeout_ms",30000)))
            await page.wait_for_timeout(int(settings.get("render_wait_ms",1200)))
            html=await page.content()
        except Exception as exc:
            print(f"AVISO {source['name']}: {url} -> {exc}")
            continue
        records.extend(discover_from_html(html,url,source,allow_youtube))
        for a in await page.locator("a[href]").all():
            try:
                href=await a.get_attribute("href")
                text=await a.inner_text()
            except Exception:
                continue
            if not href:
                continue
            u=urljoin(url,href)
            if urlparse(u).netloc==domain and u not in seen and should_follow(u,text):
                queue.append(u)
    return records
