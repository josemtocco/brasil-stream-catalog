import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

STREAM_RE = re.compile(
    r"""(?ix)
    (https?://[^"' <>\]+?\.(?:m3u8|mpd)(?:\?[^"' <>\]+)?)
    """
)

def get_soup(html):
    return BeautifulSoup(html, "lxml")

def extract_links(base_url, html):
    soup = get_soup(html)
    out = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a.get("href"))
        text = " ".join(a.stripped_strings)
        if href.startswith(("http://", "https://")):
            out.append((href, text))
    return out

def extract_streams(html, page_url):
    found = set()
    # URLs explícitas no HTML
    for match in STREAM_RE.findall(html):
        found.add(match.replace("&amp;", "&"))
    # atributos comuns de players
    soup = get_soup(html)
    attrs = ["src", "data-src", "data-url", "data-stream", "data-file", "content"]
    for tag in soup.find_all(True):
        for attr in attrs:
            value = tag.get(attr)
            if isinstance(value, str):
                for m in STREAM_RE.findall(value):
                    found.add(m.replace("&amp;", "&"))
                if value.startswith(("http://", "https://")) and (".m3u8" in value.lower() or ".mpd" in value.lower()):
                    found.add(urljoin(page_url, value))
    return sorted(found)

def title_from_page(html):
    soup = get_soup(html)
    for selector in ["h1", "h2", ".channel-title", ".title", "[class*=title]"]:
        node = soup.select_one(selector)
        if node:
            text = " ".join(node.stripped_strings)
            if 2 <= len(text) <= 120:
                return text
    if soup.title:
        return " ".join(soup.title.stripped_strings)
    return ""
