import re
from urllib.parse import urljoin
from .normalize import clean_name, slug_name

DIRECT_RE = re.compile(r"""https?://[^"'<>\s]+?\.(?:m3u8|mpd)(?:\?[^"'<>\s]*)?""", re.I)
YOUTUBE_RE = re.compile(r"""(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})""", re.I)

def direct_streams(html, base):
    out=[]
    for u in DIRECT_RE.findall(html or ""):
        u=urljoin(base,u)
        if u not in out:
            out.append(u)
    return out

def youtube_urls(html, base):
    out=[]
    for vid in YOUTUBE_RE.findall(html or ""):
        u=f"https://www.youtube.com/watch?v={vid}"
        if u not in out:
            out.append(u)
    return out

def page_name(html, fallback_url):
    patterns=[
        r"""<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)""",
        r"""<meta[^>]+name=["']twitter:title["'][^>]+content=["']([^"']+)""",
        r"""<h1[^>]*>(.*?)</h1>""",
        r"""<title[^>]*>(.*?)</title>""",
    ]
    for p in patterns:
        m=re.search(p, html or "", re.I|re.S)
        if m:
            text=re.sub("<[^>]+>"," ",m.group(1))
            n=clean_name(text)
            if n:
                return n
    return slug_name(fallback_url)
