import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests

from .extract import extract_links, extract_streams, title_from_page
from .normalize import clean_text, valid_name, infer_category

LOG = logging.getLogger(__name__)

class SourceCrawler:
    def __init__(self, source, settings):
        self.source = source
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings["user_agent"]})

    def fetch(self, url):
        try:
            r = self.session.get(url, timeout=self.settings["request_timeout"], allow_redirects=True)
            if r.status_code >= 400:
                return None, r.status_code
            return r.text, r.status_code
        except requests.RequestException as exc:
            LOG.warning("%s: %s -> %s", self.source["name"], url, exc)
            return None, 0

    def crawl(self):
        results = []
        queue = list(self.source.get("start_urls", []))
        seen = set()
        pages = 0
        while queue and pages < self.settings["max_pages_per_source"]:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)
            html, status = self.fetch(url)
            pages += 1
            if not html:
                continue

            streams = extract_streams(html, url)
            title = title_from_page(html)
            if streams and valid_name(title):
                results.append({
                    "name": clean_text(title),
                    "category": infer_category(title, url, html[:4000]),
                    "page_url": url,
                    "streams": streams,
                    "source_id": self.source["id"],
                    "source_name": self.source["name"],
                    "official_hint": bool(self.source.get("official_only"))
                })

            links = extract_links(url, html)
            base_host = urlparse(self.source["base_url"]).netloc
            for href, text in links[:self.settings["max_links_per_page"]]:
                if urlparse(href).netloc != base_host:
                    continue
                low = (href + " " + text).lower()
                # Prioriza páginas de canais e evita páginas obviamente administrativas.
                if any(x in low for x in ["canal", "canais", "tv", "live", "ao-vivo", "aovivo", "webtv", "stream"]):
                    if href not in seen and href not in queue:
                        queue.append(href)

        return results
