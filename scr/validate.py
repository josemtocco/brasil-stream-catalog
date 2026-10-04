import requests
from urllib.parse import urlparse

def validate_stream(url, timeout=10):
    host=urlparse(url).netloc.casefold()
    if "youtube.com" in host or "youtu.be" in host:
        return True
    try:
        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0","Range":"bytes=0-1024"},
                       timeout=timeout,allow_redirects=True,stream=True)
        return r.status_code < 500
    except requests.RequestException:
        return False
